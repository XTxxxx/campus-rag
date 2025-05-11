from curses import meta
from pymilvus import MilvusClient
from src.campus_rag.rag.enhance_query import enhance_query
from src.campus_rag.rag.reflect import reflect_query, ReflectionCategory
from src.campus_rag.rag.hybrid_retrieve import HybridRetriever
from src.campus_rag.rag.rerank import reranker
from src.campus_rag.rag.generate import generate_answer
from fastapi.concurrency import run_in_threadpool
from typing import AsyncGenerator
from src.campus_rag.chunk.milvus_init import (
  COLLECTION_NAME,
  MILVUS_URI,
)
import asyncio
import src.campus_rag.conversation as cm
import logging

_KEYWORDS_PATH = "./data/keywords.json"
_STATUS_PREFIX = "WLG_STATUS: "
_CONTEXT_PREFIX = "WLG_CONTEXT: "
_ANSWER_PREFIX = "WLG_ANSWER: "
_FINAL_ANSWER_PREFIX = "WLG_FINAL_ANSWER: "

logger = logging.getLogger(__name__)


class RAGPipeline:
  def __init__(self):
    self.enhance_query = enhance_query
    self.mc = MilvusClient(uri=MILVUS_URI)
    self.hybrid_retriever = HybridRetriever(mc=self.mc)
    self.collection_name = COLLECTION_NAME
    self.reranker = reranker
    self.generator = generate_answer
    self.limit = 25
    self.top_k = 5

  async def start(self, query: str, history: list[cm.ChatMessage]) -> AsyncGenerator:
    meta_info = ""

    async def _yield_wrapper(log_info: str, yield_info: str):
      nonlocal meta_info
      meta_info = meta_info + yield_info
      logger.info(log_info)
      yield yield_info
      await asyncio.sleep(0)

    # Enhance the query
    async for chunk in _yield_wrapper(
      "Enhancing query...", f"{_STATUS_PREFIX} Enhancing query...{query}\\n"
    ):
      yield chunk

    enhanced_query = await self.enhance_query(query, _KEYWORDS_PATH)

    async for chunk in _yield_wrapper(
      "Enhanced query: %s",
      f"{_STATUS_PREFIX} Enhanced query done, retrieving chunks...{enhanced_query}\\n",
    ):
      yield chunk

    # Retrieve the results
    results = await self.hybrid_retriever.retrieve(
      question=enhanced_query,
    )

    async for chunk in _yield_wrapper(
      "Length of retrieved results: %s",
      f"{_STATUS_PREFIX} Retrieving results done, reranking...\\n",
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
    split_string = "\n" + _CONTEXT_PREFIX
    results_text = _CONTEXT_PREFIX + split_string.join(extracted_topk_results)
    results_text = results_text.replace("\n", "\\n")
    results_text = "\\n" + results_text + "\\n"

    async for chunk in _yield_wrapper(
      "Length of extracted topk results: %s",
      f"{_STATUS_PREFIX} Reranking done, reflecting...",
    ):
      yield chunk

    # Reflect, detail see definition of ReflectionCategory
    reflection_result = await reflect_query(query, extracted_topk_results)

    async for chunk in _yield_wrapper(
      "Reflection result: %s",
      f"{_STATUS_PREFIX} Reflecting done, generating answer specifically...\\n {reflection_result}\\n",
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
        f"{_ANSWER_PREFIX} 抱歉，根据目前检索到的信息，我回答不了这个问题！\\n"
      )
      meta_info = meta_info + answer_text
      yield answer_text
      yield f"{_FINAL_ANSWER_PREFIX} {meta_info}\\n"
      return
    else:
      async for chunk in _yield_wrapper(
        "Returning context...",
        f"{_STATUS_PREFIX} Catch context... {results_text}",
      ):
        yield chunk

    # Generate the answer
    async for chunk in _yield_wrapper(
      "Generating answer...",
      f"{_ANSWER_PREFIX}\\n",
    ):
      yield chunk

    for res in self.generator(
      query=query,
      chunks=extracted_topk_results,
      history=history,
    ):
      cur_token = res.choices[0].delta.content
      cur_token = cur_token.replace("\n", "\\n")
      meta_info = meta_info + cur_token
      yield cur_token

    yield f"{_FINAL_ANSWER_PREFIX} {meta_info}\\n"


async def main():
  pipeline = RAGPipeline()
  query = "南哪是985吗"
  async for answer in pipeline.start(query, []):
    print(answer)


if __name__ == "__main__":
  asyncio.run(main())
