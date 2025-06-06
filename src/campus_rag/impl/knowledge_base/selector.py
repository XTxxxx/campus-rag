"""
support kinds of operations for querying knowledge base
"""

from pymilvus.milvus_client import MilvusClient
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
)
from campus_rag.infra.reranker import reranker
from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.domain.rag.po import SearchConfig
from fastapi.concurrency import run_in_threadpool
import json
from pathlib import Path

current_dir = str(Path(__file__).parent.resolve())

mc = MilvusClient(uri=MILVUS_URI)
visible_fields = {
  COLLECTION_NAME: ["id", "source", "context", "chunk", "cleaned_chunk"],
}
SOURCE_DB = current_dir + "/data/source.json"


async def get_all_collection_names() -> list[str]:
  return [COLLECTION_NAME]


async def get_all_sources() -> list[str]:
  with open(SOURCE_DB, "r", encoding="utf-8") as f:
    raw_sources = json.load(f)
  return [item["source"] for item in raw_sources]


async def get_collection_contents(
  sources: list[str], page_id: int, page_size: int
) -> list[dict]:
  expr = " OR ".join([f"source == '{source}'" for source in sources])
  total = mc.query(
    collection_name=COLLECTION_NAME,
    output_fields=["*"],
    filter=expr,
    offset=page_id * page_size,
    limit=page_size,
  )
  vis = visible_fields.get(COLLECTION_NAME, [])
  res = [{k: v for k, v in item.items() if k in vis} for item in total]
  return res


async def get_topk_results_by_query(
  query: str, sources: list[str], topk: int
) -> list[dict]:
  hr = HybridRetriever(mc, COLLECTION_NAME)
  expr = " OR ".join([f"source == {source}" for source in sources])
  config = SearchConfig(limit=topk * 2, offset=0, filter_expr=expr)
  result = await hr.retrieve(query, config)
  result = await run_in_threadpool(
    reranker.rerank,
    query=query,
    results=result,
  )
  result = result[:topk]
  vis = visible_fields.get(COLLECTION_NAME, [])
  res = [
    {
      **{k: item[k] for k in vis},
      "distance": getattr(item, "distance", None),
    }
    for item in result
  ]
  return res


# async def get_topk_results_by_query_and_filter(
#   query: str, collection_name: str, topk: int, **kwargs
# ) -> list[dict]:
#   parent_key, inner_keys, values = None, None, None
#   vis = visible_fields.get(collection_name, [])
#   if "inner_keys" in kwargs:
#     parent_key = "time_place"
#     inner_keys, values = kwargs["inner_keys"], kwargs["values"]
#     del kwargs["inner_keys"], kwargs["values"]
#   search_params = {
#     "metric_type": "IP",
#     "params": {},
#   }
#   result = await filter_with_embedding_select(
#     mc,
#     collection_name,
#     ["chunk", "meta"],
#     _type="eq",
#     query=query,
#     search_params=search_params,
#     parent_key=parent_key,
#     inner_keys=inner_keys,
#     values=values,
#     limit=topk,
#     **kwargs,
#   )
#   res = [
#     {
#       **{k: item[k] for k in vis},
#       "distance": getattr(item, "distance", None),
#     }
#     for item in result
#   ]
#   return res
