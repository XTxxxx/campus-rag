from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.domain.rag.po import SearchConfig
from campus_rag.constants.milvus import (
  COLLECTION_NAME,
  COURSES_COLLECTION_NAME,
  MILVUS_URI,
)
from campus_rag.utils.logging_config import setup_logger
from pymilvus import MilvusClient
import asyncio


logger = setup_logger()
mc = MilvusClient(uri=MILVUS_URI)


def test_hybrid_retriever():
  """Test the hybrid retriever with a sample query."""
  retriever = HybridRetriever(mc=mc, collection_name=COLLECTION_NAME)

  default_config = SearchConfig()

  # Perform a hybrid search
  results = asyncio.run(retriever.retrieve("刘嘉", default_config))
  for result in results:
    logger.info(result)
