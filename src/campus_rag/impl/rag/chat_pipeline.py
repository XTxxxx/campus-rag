from fastapi.concurrency import run_in_threadpool
from typing import AsyncGenerator
import asyncio
import logging

from campus_rag.constants.prompt import SYSTEM_PROMPT
from campus_rag.impl.rag.llm_tool.enhance_query import enhance_query
from campus_rag.impl.rag.llm_tool.reflect import reflect_query, ReflectionCategory
from campus_rag.impl.rag.llm_tool.route import route_query
from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.infra.reranker import reranker
from campus_rag.impl.rag.generate import generate_answer
from campus_rag.constants.milvus import COLLECTION_NAME
from campus_rag.constants.conversation import (
  CONTEXT_SUFFIX,
  STATUS_PREFIX,
  CONTEXT_PREFIX,
  ANSWER_PREFIX,
  TEST_PREFIX,
)
from campus_rag.domain.rag.po import ChatMessage, SearchConfig
from campus_rag.infra.milvus.init import campus_rag_mc

_KEYWORDS_PATH = "./data/keywords.json"
logger = logging.getLogger(__name__)


class ChatPipeline:
  """对话的流水线
  这个类接收用户查询、历史记录，走一遍管道，并输出流式信息
  但是不会负责对话类的管理，也就是说是stateless的
  """

  def __init__(self, test: bool = False):
    self.enhance_query = enhance_query
    self.mc = campus_rag_mc
    self.hybrid_retriever = HybridRetriever(mc=self.mc, collection_name=COLLECTION_NAME)
    self.collection_name = COLLECTION_NAME
    self.reranker = reranker
    self.async_generator = generate_answer
    self.limit = 50
    self.top_k = 5
    self.test = test
    self.available_sources = ["course", "teacher", "manual"]
    self.search_strategy = {
      "course": 5,
      "teacher": 3,
      "manual": 5,
      "global": 2,
    }

  async def minimal_start(self, query: str) -> AsyncGenerator:
    """Initializes the chat pipeline by reflecting on the system prompt."""
    search_config = SearchConfig(
      sparse_weight=0.0,
      dense_weight=1.0,
      limit=self.top_k,
      output_fields=["*"],
      filter_expr=None,
    )
    results = await self.hybrid_retriever.retrieve(
      question=query,
      config=search_config,
    )

    if self.test:
      yield TEST_PREFIX
      yield [{"id": res["id"], "chunk": res["entity"]["chunk"]} for res in results]
      return
    # TODO: Implement minimal_start generate
    pass

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

    # ENHANCE STATUS
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

    # ROUTE STATUS
    routed_sources = await route_query(enhanced_query)
    routed_sources.append("global")
    async for chunk in _yield_wrapper(
      f"Routed to sources: {routed_sources}",
      f"{STATUS_PREFIX} Routing done, target sources: {routed_sources}\\n",
    ):
      yield chunk
    logger.debug(f"Search strategy: {self.search_strategy}")

    # RETRIEVAL STATUS
    all_results = []
    seen_chunk_ids = set()
    for source in routed_sources:
      async for chunk in _yield_wrapper(
        f"Retrieving from {source}...",
        f"{STATUS_PREFIX} Retrieving from {source}...\\n",
      ):
        yield chunk
      if source != "global":
        filter_expr = f'source == "{source}"'
      else:
        filter_expr = None
      source_results = await self.hybrid_retriever.retrieve(
        question=enhanced_query,
        config=SearchConfig(
          limit=self.limit,
          output_fields=["*"],
          filter_expr=filter_expr,
        ),
      )
      source_reranked = await run_in_threadpool(
        self.reranker.rerank,
        query=enhanced_query,
        results=source_results,
      )
      source_topk = []
      for result in source_reranked[: self.search_strategy[source]]:
        chunk_id = result.get("id")
        if chunk_id not in seen_chunk_ids:
          source_topk.append(result)
          seen_chunk_ids.add(chunk_id)
      all_results.extend(source_topk)
      async for chunk in _yield_wrapper(
        f"Retrieved {len(source_topk)} unique chunks from {source}",
        f"{STATUS_PREFIX} Retrieved {len(source_topk)} chunks from {source}\\n",
      ):
        yield chunk

    async for chunk in _yield_wrapper(
      f"Total unique chunks retrieved: {len(all_results)}",
      f"{STATUS_PREFIX} Total unique chunks retrieved: {len(all_results)}\\n",
    ):
      yield chunk
    if self.test:
      # Rerank all chunks
      all_reranked = await run_in_threadpool(
        self.reranker.rerank,
        query=enhanced_query,
        results=all_results,
      )
      chunks = [
        {"id": res["id"], "chunk": res["entity"]["chunk"]} for res in all_reranked
      ]
      test_result = f"{TEST_PREFIX} Test mode, returning chunk IDs: \\n"
      yield test_result
      yield chunks
    extracted_topk_results = [res["entity"]["chunk"] for res in all_results]
    split_string = "\n"
    for i, chunk in enumerate(extracted_topk_results):
      extracted_topk_results[i] = f"{CONTEXT_PREFIX}{chunk}{CONTEXT_SUFFIX}"
    results_text = split_string.join(extracted_topk_results)
    results_text = results_text.replace("\n", "\\n")
    results_text = results_text.replace("\r", "\\n")
    results_text = "\\n" + results_text + "\\n"
    logger.debug(f"Results text: {results_text}")
    async for chunk in _yield_wrapper(
      f"Length of extracted topk results: {len(extracted_topk_results)}",
      f"{STATUS_PREFIX} Reranking done, reflecting...",
    ):
      yield chunk

    async for chunk in _yield_wrapper(
      "Returning context...",
      f"{STATUS_PREFIX} Collecting context... {results_text}",
    ):
      yield chunk

    # Generate the answer
    async for chunk in _yield_wrapper(
      "Generating answer...",
      f"{ANSWER_PREFIX}\\n",
    ):
      yield chunk
    stream = await self.async_generator(
      query=query, chunks=extracted_topk_results, history=history
    )
    async for token in stream:
      token = token.replace("\n", "\\n")
      yield token
