from pymilvus import MilvusClient, DataType
from campus_rag.constants.milvus import MILVUS_URI, COLLECTION_NAME
from campus_rag.infra.embedding import sparse_embedding_model, embedding_model
from campus_rag.utils.chunk_ops import construct_embedding_key
import logging
import json
from pathlib import Path

current_dir = str(Path(__file__).parent.resolve())

mc = MilvusClient(uri=MILVUS_URI)
_MAX_LENGTH = 65535
SOURCE_DB = current_dir + "/data/source.json"


async def _construct_embedding_key(
  chunk: dict, chunk_keys: list[str], max_value_size: int
):
  embedding_keys = ""
  for key in chunk_keys:
    value = chunk.get(key, "")
    _value = value if len(value) <= max_value_size else value[:max_value_size] + "..."
    embedding_keys += f"{key}: {_value}, "
  if embedding_keys.endswith(", "):
    embedding_keys = embedding_keys[:-2]
  return embedding_keys


async def _create_collection(collection_name: str):
  if mc.has_collection(collection_name):
    mc.drop_collection(collection_name)
  schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=True)
  schema.add_field("id", DataType.INT64, is_primary=True)
  schema.add_field(
    "embedding",
    DataType.FLOAT_VECTOR,
    dim=embedding_model.get_sentence_embedding_dimension(),
  )
  schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
  schema.add_field("chunk", DataType.VARCHAR, max_length=_MAX_LENGTH)
  index_params = mc.prepare_index_params()
  index_params.add_index(field_name="embedding", index_type="FLAT", metric_type="IP")
  index_params.add_index(
    field_name="sparse_embedding",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="IP",
  )
  mc.create_collection(
    collection_name=collection_name, schema=schema, index_params=index_params
  )
  logging.log(f"Successfully created collection {collection_name}")


async def upload(
  sources: list[str],
  knowledge: list[dict],
) -> bool:
  try:
    # await _create_collection(collection_name)
    insert_datas = []
    with open(SOURCE_DB, "r", encoding="utf-8") as f:
      raw_sources = json.load(f)
    for source in sources:
      if source not in [item["source"] for item in raw_sources]:
        raw_sources.append({"source": source})
    with open(SOURCE_DB, "w", encoding="utf-8") as f:
      json.dump(raw_sources, f)
    for chunk in knowledge:
      embedding_keys = construct_embedding_key(chunk)
      embeddings = embedding_model.encode(embedding_keys)
      sparse_embeddings = sparse_embedding_model([embedding_keys])["sparse"]
      insert_datas.append(
        {
          "embedding": embeddings,
          "sparse_embedding": sparse_embeddings,
          "source": chunk["source"],
          "context": " ".join(chunk["context"]),
          "cleaned_chunk": chunk["cleaned_chunk"],
          "chunk": chunk["chunk"],
          "id": chunk["id"],
        }
      )
    mc.upsert(
      collection_name=COLLECTION_NAME,
      data=insert_datas,
    )
    # immediately flush for search
    mc.flush(collection_name=COLLECTION_NAME)
    return True
  except Exception as e:
    logging.error(e)
    return False


# async def get_chunk_ids_by_collection_name(collection_name: str) -> list[int]:
#   offset = 0
#   res = []
#   limit = 10
#   while True:
#     page = mc.query(
#       collection_name=collection_name,
#       filter="",
#       output_fields=["id"],
#       limit=limit,
#       offset=offset,
#     )
#     offset += limit
#     res.extend(page)
#     if len(page) < limit:
#       break
#   return [str(item["id"]) for item in res]


# async def get_chunk_by_id(collection_name: str, chunk_id: int) -> str:
#   res = mc.query(
#     collection_name=collection_name,
#     filter=f"id == {chunk_id}",
#     output_fields=["chunk"],
#     limit=1,
#   )[0]
#   return res["chunk"]


async def modify(
  request_id: str, context: str = None, chunk: str = None, cleaned_chunk: str = None
) -> bool:
  try:
    expr = f"id == '{request_id}'"
    res = mc.query(
      collection_name=COLLECTION_NAME,
      filter=expr,
      output_fields=["*"],
      limit=1,
    )[0]
    embedding_key = res["source"]
    embedding_key += res["context"] if not context else context
    if res["cleaned_chunk"] != "" or (cleaned_chunk and cleaned_chunk != ""):
      embedding_key += res["cleaned_chunk"] if not cleaned_chunk else cleaned_chunk
    else:
      embedding_key += res["chunk"] if not chunk else chunk
    embeddings = embedding_model.encode(embedding_key)
    sparse_embeddings = sparse_embedding_model([embedding_key])["sparse"]
    new_data = [
      {
        "embedding": embeddings,
        "sparse_embedding": sparse_embeddings,
        "source": res["source"],
        "context": res["context"] if not context else context,
        "cleaned_chunk": res["cleaned_chunk"] if (not cleaned_chunk or cleaned_chunk == "") else cleaned_chunk,
        "chunk": res["chunk"] if not chunk else chunk,
        "id": request_id,
      }
    ]
    mc.upsert(
      collection_name=COLLECTION_NAME,
      data=new_data,
    )
    return True
  except Exception as e:
    logging.error(e)
    return False
