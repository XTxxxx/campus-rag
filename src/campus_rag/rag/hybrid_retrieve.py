from pymilvus import (
  AnnSearchRequest,
  MilvusClient,
  WeightedRanker,
)
from typing import List
from src.campus_rag.utils.chunk_ops import construct_embedding_key
from src.campus_rag.chunk.milvus_init import (
  COLLECTION_NAME,
  embedding_model,
  sparse_embedding_model,
)


class HybridRetriever:
  """
  TODO: Finetune sparse / dense weights for better performance.
  """

  def hybrid_search(
    self,
    col: str,
    query: str,
    sources: str,
    limit: int,
    config,
  ) -> List[dict]:
    sparse_weight = config["sparse_weight"]
    dense_weight = config["dense_weight"]
    do_title_filter = config["do_title_filter"]
    query_dense_embedding = embedding_model.encode(query, normalize_embeddings=True)
    query_sparse_embedding = sparse_embedding_model([query])["sparse"][[0]]
    dense_search_params = {"metric_type": "IP", "params": {}}
    expr = None
    if do_title_filter and sources:
      expr = f"source in {sources}"
    # Dense vector for semantic search
    dense_req = AnnSearchRequest(
      [query_dense_embedding],
      "embedding",
      dense_search_params,
      limit=limit,
      expr=expr,
    )
    # Sparse vector for keyword search
    sparse_search_params = {"metric_type": "IP", "params": {}}
    sparse_req = AnnSearchRequest(
      [query_sparse_embedding],
      "sparse_embedding",
      sparse_search_params,
      limit=limit,
      expr=expr,
    )
    req_list = [sparse_req, dense_req]
    rerank = WeightedRanker(sparse_weight, dense_weight)
    res = self.mc.hybrid_search(
      col,
      req_list,
      ranker=rerank,
      limit=limit,
      output_fields=[
        "source",
        "chunk",
        "cleaned_chunk",
        "context",
      ],
    )[0]
    return res

  def __init__(self, mc: MilvusClient, is_test=False):
    self.mc = mc
    self.is_test = is_test
    self.config = {
      "sparse_weight": 1.0,
      "dense_weight": 0.5,
      "do_title_filter": True,
    }
    self.without_filter_config = {
      "sparse_weight": 1.0,
      "dense_weight": 0.5,
      "do_title_filter": False,
    }

  def retrieve(self, question, limit=25, sources=None, col=COLLECTION_NAME):
    # Search with filters
    hybrid_results = self.hybrid_search(
      col, question, sources, limit, self.config
    )
    # If no results found, search without filters
    if len(hybrid_results) == 0:
      hybrid_results = self.hybrid_search(
        col, question, sources, limit, self.without_filter_config
      )
    return hybrid_results
