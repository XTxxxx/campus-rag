from pymilvus import MilvusClient
from fastapi.concurrency import run_in_threadpool
from typing import AsyncGenerator, Callable
import asyncio
import logging

from campus_rag.constants.prompt import SYSTEM_PROMPT
from campus_rag.impl.rag.llm_tool.enhance_query import enhance_query
from campus_rag.impl.rag.llm_tool.reflect import reflect_query, ReflectionCategory
from campus_rag.impl.rag.hybrid_retrieve import HybridRetriever
from campus_rag.infra.reranker import reranker
from campus_rag.impl.rag.generate import generate_answer
from campus_rag.constants.milvus import COLLECTION_NAME, MILVUS_URI
from campus_rag.constants.conversation import (
  STATUS_PREFIX,
  CONTEXT_PREFIX,
  ANSWER_PREFIX,
)
from campus_rag.domain.rag.po import ChatMessage

_KEYWORDS_PATH = "./data/keywords.json"
logger = logging.getLogger(__name__)


class ConverstaionPipeline:
  """对话的流水线
  这个类接收用户查询、历史记录，走一遍管道，并输出流式信息
  但是不会负责对话类的管理，也就是说是stateless的
  """

  def __init__(self):
    self.enhance_query = enhance_query
    self.mc = MilvusClient(uri=MILVUS_URI)
    self.hybrid_retriever = HybridRetriever(mc=self.mc)
    self.collection_name = COLLECTION_NAME
    self.reranker = reranker
    self.async_generator = generate_answer
    self.limit = 25
    self.top_k = 5

  async def start(self, query: str, history: list[ChatMessage]) -> AsyncGenerator:
    async def _yield_wrapper(log_info: str, yield_info: str):
      """
      A wrapper function to yield information while logging the process.

      Args:
          log_info (str): Information to log.
          yield_info (str): Information to yield.

      Yields:
          str: The information to yield.
      """
      logger.debug(log_info)
      yield yield_info
      await asyncio.sleep(0)

    # Enhance the query
    async for chunk in _yield_wrapper(
      "Enhancing query...", f"{STATUS_PREFIX} Enhancing query...{query}\\n"
    ):
      yield chunk

    enhanced_query = await self.enhance_query(query, _KEYWORDS_PATH)

    async for chunk in _yield_wrapper(
      f"Enhanced query: {enhanced_query}",
      f"{STATUS_PREFIX} Enhanced query done, retrieving chunks...{enhanced_query}\\n",
    ):
      yield chunk

    # Retrieve the results
    results = await self.hybrid_retriever.retrieve(
      question=enhanced_query,
    )

    async for chunk in _yield_wrapper(
      f"Length of retrieved results: {len(results)}",
      f"{STATUS_PREFIX} Retrieving results done, reranking...\\n",
    ):
      yield chunk

    # Rerank
    results = await run_in_threadpool(
      self.reranker.rerank,
      query=enhanced_query,
      results=results,
    )
    topk_results = results[: self.top_k]
    extracted_topk_results = [res["entity"]["chunk"] for res in topk_results]
    split_string = "\n" + CONTEXT_PREFIX
    results_text = CONTEXT_PREFIX + split_string.join(extracted_topk_results)
    results_text = results_text.replace("\n", "\\n")
    results_text = "\\n" + results_text + "\\n"

    async for chunk in _yield_wrapper(
      f"Length of extracted topk results: {len(extracted_topk_results)}",
      f"{STATUS_PREFIX} Reranking done, reflecting...",
    ):
      yield chunk

    # Reflect, detail see definition of ReflectionCategory
    reflection_result = await reflect_query(query, extracted_topk_results, SYSTEM_PROMPT)

    async for chunk in _yield_wrapper(
      f"Reflection result: {reflection_result}",
      f"{STATUS_PREFIX} Reflecting done, generating answer specifically...\\n {reflection_result}\\n",
    ):
      yield chunk

    if reflection_result["category"] == ReflectionCategory.IRRELEVANT.value:
      # Irrelevant question, use context free metainfo and remove the context
      extracted_topk_results = []
    elif (
      reflection_result["category"] == ReflectionCategory.RELEVANT_INSUFFICIENT.value
    ):
      # Relevant but insufficient question, use context free metainfo and need not generate answer
      answer_text = (
        f"{ANSWER_PREFIX} 抱歉，根据目前检索到的信息，我回答不了这个问题！\\n"
      )
      yield answer_text
      return
    else:
      async for chunk in _yield_wrapper(
        "Returning context...",
        f"{STATUS_PREFIX} Catch context... {results_text}",
      ):
        yield chunk

    # Generate the answer
    async for chunk in _yield_wrapper(
      "Generating answer...",
      f"{ANSWER_PREFIX}\\n",
    ):
      yield chunk

    stream = await self.async_generator(
      query=enhanced_query, chunks=extracted_topk_results, history=history
    )

    async for token in stream:
      token = token.replace("\n", "\\n")
      yield token
