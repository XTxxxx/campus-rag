"""
support kinds of operations for querying knowledge base
"""

from pymilvus.milvus_client import MilvusClient
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
  COLLECTION_NAME,
  COLLECTIONS,
)
from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.domain.rag.po import SearchConfig
from campus_rag.infra.milvus.course_ops import filter_with_embedding_select

mc = MilvusClient(uri=MILVUS_URI)
visible_fields = {
  COLLECTION_NAME: ["source", "chunk"],
  COLLECTION_NAME: ["meta"],
}


async def get_all_collection_names() -> list[str]:
  return COLLECTIONS


async def get_collection_contents(
  collection_name: str, page_id: int, page_size: int
) -> list[dict]:
  total = mc.query(
    collection_name=collection_name,
    output_fields=["*"],
    offset=page_id * page_size,
    limit=page_size,
  )
  vis = visible_fields.get(collection_name, [])
  res = [{k: v for k, v in item.items() if k in vis} for item in total]
  breakpoint()
  return res


async def get_topk_results_by_query(
  query: str, collection_name: str, topk: int
) -> list[dict]:
  hr = HybridRetriever(mc, collection_name)
  config = SearchConfig(limit=topk, offset=0)
  result = await hr.retrieve(query, config)
  vis = visible_fields.get(collection_name, [])
  res = [
    {
      **{k: item[k] for k in vis},
      "distance": getattr(item, "distance", None),
    }
    for item in result
  ]
  return res


async def get_topk_results_by_query_and_filter(
  query: str, collection_name: str, topk: int, **kwargs
) -> list[dict]:
  parent_key, inner_keys, values = None, None, None
  vis = visible_fields.get(collection_name, [])
  if "inner_keys" in kwargs:
    parent_key = "time_place"
    inner_keys, values = kwargs["inner_keys"], kwargs["values"]
    del kwargs["inner_keys"], kwargs["values"]
  search_params = {
    "metric_type": "IP",
    "params": {},
  }
  result = await filter_with_embedding_select(
    mc,
    collection_name,
    ["chunk", "meta"],
    _type="eq",
    query=query,
    search_params=search_params,
    parent_key=parent_key,
    inner_keys=inner_keys,
    values=values,
    limit=topk,
    **kwargs,
  )
  res = [
    {
      **{k: item[k] for k in vis},
      "distance": getattr(item, "distance", None),
    }
    for item in result
  ]
  return res
