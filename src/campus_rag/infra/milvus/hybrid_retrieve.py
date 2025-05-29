from pymilvus import (
  AnnSearchRequest,
  MilvusClient,
  WeightedRanker,
)
from typing import List
from campus_rag.infra.embedding import embedding_model, sparse_embedding_model
from fastapi.concurrency import run_in_threadpool
from campus_rag.domain.rag.po import SearchConfig


class HybridRetriever:
  """
  TODO: Finetune sparse / dense weights for better performance.
  """

  def __init__(self, mc: MilvusClient, collection_name: str, is_test=False):
    self.mc = mc
    self.collection_name = collection_name
    self.is_test = is_test

  def _hybrid_search(
    self,
    query: str,
    config: SearchConfig,
  ) -> List[dict]:
    sparse_weight = config.sparse_weight
    dense_weight = config.dense_weight
    query_dense_embedding = embedding_model.encode(query, normalize_embeddings=True)
    query_sparse_embedding = sparse_embedding_model([query])["sparse"][[0]]
    dense_search_params = {"metric_type": "IP", "params": {}}
    expr = config.filter_expr
    limit = config.limit
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
      self.collection_name,
      req_list,
      ranker=rerank,
      limit=limit,
      output_fields=config.output_fields,
      offset=config.offset,
    )[0]
    return res

  async def retrieve(self, question: str, config: SearchConfig) -> List[dict]:
    # Search with filters
    hybrid_results = await run_in_threadpool(self._hybrid_search, question, config)
    # Delete the embedding and sparse_embedding fields from the results
    for result in hybrid_results:
      if "embedding" in result:
        del result["embedding"]
      if "embedding" in result["entity"]:
        del result["entity"]["embedding"]
      if "sparse_embedding" in result:
        del result["sparse_embedding"]
      if "sparse_embedding" in result["entity"]:
        del result["entity"]["sparse_embedding"]
    return hybrid_results
