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

from campus_rag.utils.chunk_ops import construct_embedding_key
from campus_rag.utils.logging_config import setup_logger
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
  COURSES_COLLECTION_NAME,
)
from ..embedding import embedding_model, sparse_embedding_model

import typer
import os
import json

from pymilvus import DataType, MilvusClient
from tqdm import tqdm

app = typer.Typer()
logger = setup_logger("info")


_MAX_LENGTH = 65535
_DATA_ROOT = "./data"


def create_collections(mc: MilvusClient):
  """
  Drop the collection if it exists and create a new one.
  """
  if mc.has_collection(COLLECTION_NAME):
    mc.drop_collection(COLLECTION_NAME)
    logger.info(f"Successfully dropped collection {COLLECTION_NAME}")
  schema = MilvusClient.create_schema(
    auto_id=True,
    enable_dynamic_field=True,
  )
  schema.add_field("id", DataType.INT64, is_primary=True)
  schema.add_field(
    "embedding",
    DataType.FLOAT_VECTOR,
    dim=embedding_model.get_sentence_embedding_dimension(),
  )
  # Refer to https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-enrichment-phase for details
  # sparse embedding: sparse vector used for keyword search
  schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
  # source: where the chunk comes from, used for routing
  schema.add_field("source", DataType.VARCHAR, max_length=_MAX_LENGTH)
  schema.add_field("chunk", DataType.VARCHAR, max_length=_MAX_LENGTH)
  schema.add_field("cleaned_chunk", DataType.VARCHAR, max_length=_MAX_LENGTH)
  schema.add_field("context", DataType.VARCHAR, max_length=_MAX_LENGTH)

  # create indexes
  index_params = mc.prepare_index_params()
  index_params.add_index(field_name="embedding", index_type="FLAT", metric_type="IP")
  index_params.add_index(
    field_name="source",
  )
  index_params.add_index(
    field_name="sparse_embedding", index_type="SPARSE_INVERTED_INDEX", metric_type="IP"
  )

  mc.create_collection(
    collection_name=COLLECTION_NAME, schema=schema, index_params=index_params
  )
  logger.info(f"Successfully created collection {COLLECTION_NAME}")


def insert_data(mc: MilvusClient):
  """
  Insert data into the collection.
  """
  datas = ["nju_se_teacher.json", "red_and_black_table.json"]
  logger.info("Inserting data into Milvus")
  for data in datas:
    data_path = os.path.join(_DATA_ROOT, data)
    with open(data_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    for chunk in tqdm(data):
      embedding_key = construct_embedding_key(chunk)
      mc.insert(
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
  logger.info("Successfully inserted data into Milvus")


@app.command()
def all():
  mc = MilvusClient(uri=MILVUS_URI)
  create_collections(mc)
  insert_data(mc)


@app.command()
def example():
  logger.info("Inserting example data into Milvus")
  mc = MilvusClient(uri=MILVUS_URI)
  create_collections(mc)
  example_path = os.path.join(_DATA_ROOT, "example.json")
  with open(example_path, "r", encoding="utf-8") as f:
    data = json.load(f)
  for chunk in tqdm(data):
    embedding_key = construct_embedding_key(chunk)
    mc.insert(
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


if __name__ == "__main__":
  app()
