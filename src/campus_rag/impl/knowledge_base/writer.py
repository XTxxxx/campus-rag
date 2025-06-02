from pymilvus import MilvusClient, DataType
from campus_rag.constants.milvus import MILVUS_URI
from campus_rag.infra.embedding import sparse_embedding_model, embedding_model
import logging

mc = MilvusClient(uri=MILVUS_URI)
_MAX_LENGTH = 65535


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
  collection_name: str,
  knowledge: list[dict],
  chunk_keys: list[str],
  max_value_size: int,
  meta_field: bool,
) -> bool:
  try:
    await _create_collection(collection_name)
    insert_datas = []
    for chunk in knowledge:
      embedding_keys = await _construct_embedding_key(chunk, chunk_keys, max_value_size)
      embeddings = embedding_model.encode(embedding_keys)
      sparse_embeddings = sparse_embedding_model([embedding_keys])["sparse"]
      insert_datas.append(
        {
          "embedding": embeddings,
          "sparse_embedding": sparse_embeddings,
          "chunk": embedding_keys,
          **({"meta": chunk} if meta_field else {}),
        }
      )
    mc.insert(
      collection_name=collection_name,
      data=insert_datas,
    )
    return True
  except Exception as e:
    logging.error(e)
    return False


async def get_chunk_ids_by_collection_name(collection_name: str) -> list[int]:
  res = mc.query(collection_name=collection_name, output_fields=["id"])
  return [int(item["id"]) for item in res]


async def get_chunk_by_id(collection_name: str, chunk_id: int) -> str:
  res = mc.query(
    collection_name=collection_name,
    filter=f"id == {chunk_id}",
    output_fields=["chunk"],
    limit=1,
  )[0]
  return res["chunk"]


async def modify_chunk_by_id(
  collection_name: str, chunk_id: int, new_chunk: str
) -> bool:
  try:
    embeddings = embedding_model.encode(new_chunk)
    sparse_embeddings = sparse_embedding_model([new_chunk])["sparse"]
    # select possible meta field
    meta = {}
    res = mc.query(
      collection_name=collection_name,
      filter=f"id == {chunk_id}",
      output_fields=["*"],
      limit=1,
    )[0]
    if "meta" in res.keys():
      meta = {"meta": res["meta"]}
    new_data = [
      {
        "id": chunk_id,
        "embedding": embeddings,
        "sparse_embedding": sparse_embeddings,
        "chunk": new_chunk,
        **meta,
      }
    ]
    mc.upsert(
      collection_name=collection_name,
      data=new_data,
    )
    return True
  except Exception as e:
    logging.error(e)
    return False
