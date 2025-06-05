from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.domain.rag.po import SearchConfig
from campus_rag.constants.milvus import (
  COLLECTION_NAME,
  COLLECTION_NAME,
  MILVUS_URI,
)
from campus_rag.utils.logging_config import setup_logger
from pymilvus import MilvusClient
from campus_rag.infra.milvus.init import campus_rag_mc
import asyncio


logger = setup_logger()


def test_hybrid_retriever():
  """Test the hybrid retriever with a sample query."""
  retriever = HybridRetriever(mc=campus_rag_mc, collection_name=COLLECTION_NAME)

  default_config = SearchConfig()

  # Perform a hybrid search
  results = asyncio.run(retriever.retrieve("刘嘉", default_config))
  for result in results:
    logger.info(result)
