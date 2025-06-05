"""
This script is used to create a Milvus collection and insert data into it.
Datas are stored in the `data` folder (in json format).

Usage:
- Start Milvus server:
  `cd milvus-standalone`
  `docker compuse up -d`
- To create a collection and insert data:
  `python milvus_init.py all`

TODO: add more collections(maybe not necessary), insert real data crawled from the nju websites
"""

from sqlalchemy import null
from campus_rag.utils.chunk_ops import (
  construct_embedding_key,
  construct_embedding_key_for_course,
  construct_meta_for_course,
)
from campus_rag.utils.logging_config import setup_logger
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
  COURSES_COLLECTION_NAME,
  INSERT_BATCH_SIZE,
)
from ..embedding import embedding_model, sparse_embedding_model

import typer
import os
import json

from pymilvus import DataType, MilvusClient
from tqdm import tqdm

app = typer.Typer()
logger = setup_logger("info")
campus_rag_mc = MilvusClient(uri=MILVUS_URI)


_MAX_LENGTH = 65535
_DATA_ROOT = "./data"

collections = [COLLECTION_NAME, COURSES_COLLECTION_NAME]


def create_collections():
  """Create Milvus collections for conversation and course data.
  Use milvus's dynamic field feature to create a collection with dynamic fields.
  Meta would be stored as json in dynamic field.
  """
  for collection in collections:
    if campus_rag_mc.has_collection(collection):
      campus_rag_mc.drop_collection(collection)
      logger.info(f"Successfully dropped collection {collection}")
    schema = MilvusClient.create_schema(
      enable_dynamic_field=True,
    )
    schema.add_field("id", DataType.VARCHAR, max_length=_MAX_LENGTH, is_primary=True)
    schema.add_field(
      "embedding",
      DataType.FLOAT_VECTOR,
      dim=embedding_model.get_sentence_embedding_dimension(),
    )
    # Refer to https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-enrichment-phase for details
    # sparse embedding: sparse vector used for keyword search
    schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
    # source: where the chunk comes from, used for routing
    schema.add_field("source", DataType.VARCHAR, max_length=_MAX_LENGTH, nullable=True)
    schema.add_field("chunk", DataType.VARCHAR, max_length=_MAX_LENGTH)
    schema.add_field(
      "cleaned_chunk", DataType.VARCHAR, max_length=_MAX_LENGTH, nullable=True
    )
    schema.add_field("context", DataType.VARCHAR, max_length=_MAX_LENGTH, nullable=True)

    # create indexes
    index_params = campus_rag_mc.prepare_index_params()
    index_params.add_index(field_name="embedding", index_type="FLAT", metric_type="IP")
    index_params.add_index(
      field_name="source",
    )
    index_params.add_index(
      field_name="sparse_embedding",
      index_type="SPARSE_INVERTED_INDEX",
      metric_type="IP",
    )

    campus_rag_mc.create_collection(
      collection_name=collection, schema=schema, index_params=index_params
    )
    logger.info(f"Successfully created collection {collection}")


def upsert_chat(
  datas: list = [
    "nju_se_teacher.json",
    "student_manual.json",
  ],
):
  """
  Insert data into the collection.
  """
  logger.info(f"Inserting data from {datas} into Milvus")
  for data in datas:
    data_path = os.path.join(_DATA_ROOT, data)
    with open(data_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    for chunk in tqdm(data):
      embedding_key = construct_embedding_key(chunk)
      campus_rag_mc.upsert(
        collection_name=COLLECTION_NAME,
        data={
          "embedding": embedding_model.encode(embedding_key),
          "sparse_embedding": sparse_embedding_model([embedding_key])["sparse"],
          "source": chunk["source"],
          "context": " ".join(chunk["context"]),
          "cleaned_chunk": chunk["cleaned_chunk"],
          "chunk": chunk["chunk"],
          "id": chunk["id"],
        },
      )
  logger.info("Successfully inserted data into Milvus")


def upsert_course_data():
  """
  Insert course data into the collection.
  Maybe other collections should be refactored into structure like this.
  """
  data_path = os.path.join(_DATA_ROOT, "course_list.json")
  course_id = 0
  with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)
  for batch_idx in tqdm(
    range(0, len(data), INSERT_BATCH_SIZE), desc="batch inserting courses"
  ):
    # Every batch embedding and insert together
    batch = data[batch_idx : batch_idx + INSERT_BATCH_SIZE]
    embedding_keys = [construct_embedding_key_for_course(chunk) for chunk in batch]
    embeddings = embedding_model.encode(embedding_keys)
    sparse_embeddings = sparse_embedding_model(embedding_keys)["sparse"]
    chunk_ids = [chunk["id"] for chunk in batch]
    metas = [construct_meta_for_course(chunk) for chunk in batch]
    for meta in metas:
      meta["course_id"] = course_id
      course_id += 1
    to_insert = [
      {
        "embedding": embeddings[i],
        "sparse_embedding": sparse_embeddings[i : i + 1],
        "source": "课程数据",
        "context": "",
        "chunk": embedding_keys[i],
        "id": chunk_ids[i],
        "meta": metas[i],
      }
      for i in range(len(batch))
    ]
    campus_rag_mc.insert(
      collection_name=COURSES_COLLECTION_NAME,
      data=to_insert,
    )
    campus_rag_mc.insert(collection_name=COLLECTION_NAME, data=to_insert)

  logger.info("Successfully inserted course data into Milvus")


@app.command()
def all():
  create_collections()
  upsert_chat()
  upsert_course_data()


@app.command()
def example():
  logger.info("Inserting example data into Milvus")
  create_collections()
  example_path = os.path.join(_DATA_ROOT, "example.json")
  with open(example_path, "r", encoding="utf-8") as f:
    data = json.load(f)
  for chunk in tqdm(data):
    embedding_key = construct_embedding_key(chunk)
    campus_rag_mc.insert(
      collection_name=COLLECTION_NAME,
      data={
        "embedding": embedding_model.encode(embedding_key),
        "sparse_embedding": sparse_embedding_model([embedding_key])["sparse"],
        "source": chunk["source"],
        "context": " ".join(chunk["context"]),
        "cleaned_chunk": chunk["cleaned_chunk"],
        "chunk": chunk["chunk"],
      },
    )


@app.command()
def upsert_teacher():
  upsert_chat(datas=["nju_se_teacher.json"])


if __name__ == "__main__":
  app()
