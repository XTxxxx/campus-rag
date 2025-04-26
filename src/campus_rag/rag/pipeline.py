from pymilvus import MilvusClient
from src.campus_rag.rag.enhance_query import enhance_query
from src.campus_rag.rag.reflect import reflect_query, ReflectionCategory
from src.campus_rag.rag.hybrid_retrieve import HybridRetriever
from src.campus_rag.rag.rerank import reranker
from src.campus_rag.rag.generate import generate_answer
from typing import AsyncGenerator
from src.campus_rag.chunk.milvus_init import (
  COLLECTION_NAME,
  MILVUS_URI,
)
import asyncio
import src.campus_rag.conversation as cm

_KEYWORDS_PATH = "./data/keywords.json"
_STATUS_PREFIX = "WLG_STATUS: "
_CONTEXT_PREFIX = "WLG_CONTEXT: "
_ANSWER_PREFIX = "WLG_ANSWER: "
_FINAL_ANSWER_PREFIX = "WLG_FINAL_ANSWER: "


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
    # Enhance the query
    yield f"{_STATUS_PREFIX} Enhancing query...{query}\\n"
    enhanced_query = await self.enhance_query(query, _KEYWORDS_PATH)
    yield f"{_STATUS_PREFIX} Enhancing query done, retrieving chunks...{enhanced_query}\\n"
    # Retrieve the results
    results = await self.hybrid_retriever.retrieve(
      question=enhanced_query,
    )
    yield f"{_STATUS_PREFIX} Retrieving results done, reranking...\\n"
    # Rerank
    results = self.reranker.rerank(
      query=enhanced_query,
      results=results,
    )
    topk_results = results[: self.top_k]
    extracted_topk_results = [res["entity"]["chunk"] for res in topk_results]
    results_text = "\n\n".join(extracted_topk_results)
    results_text = results_text.replace("\n", "\\n")
    yield f"{_STATUS_PREFIX} Reranking done, reflecting...\\n{_CONTEXT_PREFIX}: {results_text}\\n"
    # Reflect, detail see definition of ReflectionCategory
    reflection_result = await reflect_query(query, extracted_topk_results)
    yield f"{_STATUS_PREFIX} Reflecting done, generating answer specifically...\\n"

    if reflection_result["category"] == ReflectionCategory.IRRELEVANT.value:
      extracted_topk_results = []

    if reflection_result["category"] == ReflectionCategory.RELEVANT_INSUFFICIENT.value:
      yield f"{_ANSWER_PREFIX} 抱歉，根据目前检索到的信息，我回答不了这个问题！\\n"
      return

    # Generate the answer
    yield f"{_ANSWER_PREFIX}\\n"
    answer = ""
    for res in self.generator(
      query=query,
      chunks=extracted_topk_results,
      history=history,
    ):
      cur_token = res.choices[0].delta.content
      cur_token = cur_token.replace("\n", "\\n")
      yield cur_token
      answer += cur_token
    yield f"{_FINAL_ANSWER_PREFIX} {answer}"


async def main():
  pipeline = RAGPipeline()
  query = "南哪是985吗"
  async for answer in pipeline.start(query, []):
    print(answer)


if __name__ == "__main__":
  asyncio.run(main())
