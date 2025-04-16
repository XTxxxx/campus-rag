from pymilvus import MilvusClient
from src.campus_rag.rag.enhance_query import enhance_query
from src.campus_rag.rag.hybrid_retrieve import HybridRetriever
from src.campus_rag.rag.rerank import reranker
from src.campus_rag.rag.generate import generate_answer
from src.campus_rag.utils.chunk_ops import get_chunk
from typing import AsyncGenerator
from src.campus_rag.chunk.milvus_init import (
  COLLECTION_NAME,
  MILVUS_URI,
)
import asyncio
import src.campus_rag.conversation as cm

_KEYWORDS_PATH = "./data/keywords.json"


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
    yield f"status: Enhancing query...{query}\n"
    enhanced_query = self.enhance_query(query, _KEYWORDS_PATH)
    yield f"status: Enhancing query done, retrieving chunks...{enhanced_query}\n"
    # Retrieve the results
    results = self.hybrid_retriever.retrieve(
      question=enhanced_query,
    )
    yield f"status: Retrieving results done, reranking...Got {len(results)} results.\n"
    # Rerank
    results = self.reranker.rerank(
      query=enhanced_query,
      results=results,
    )
    yield "status: Reranking done, generating answer...\n"
    # Generate the answer
    yield "answer: \n"
    answer = ""
    for res in self.generator(
      query=query,
      chunks=[get_chunk(res["entity"]) for res in results[: self.top_k]],
      history=history,
    ):
      cur_token = res.choices[0].delta.content
      yield cur_token
      answer += cur_token
    yield f"final answer:\n{answer}\n"


async def main():
  pipeline = RAGPipeline()
  query = "南哪是985吗"
  async for answer in pipeline.start(query, []):
    print(answer)


if __name__ == "__main__":
  asyncio.run(main())
