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

from src.campus_rag.utils.chunk_ops import construct_embedding_key
from src.campus_rag.utils.logging_config import configure_logger
from sentence_transformers import SentenceTransformer  # noqa
from milvus_model.hybrid import BGEM3EmbeddingFunction  # noqa

import typer
import os
import json
import logging
from pathlib import Path

from pymilvus import DataType, MilvusClient, FieldSchema
from tqdm import tqdm
from src.campus_rag.utils.const import *
from src.campus_rag.utils.milvus_ops import create_course_collection

app = typer.Typer()
configure_logger("info")
logger = logging.getLogger(__name__)


COLLECTION_NAME = "example"
MILVUS_URI = "http://localhost:19530"
_MAX_LENGTH = 65535
logger.info("Loading embedding model...")
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
sparse_embedding_model = BGEM3EmbeddingFunction(device="cuda:0")
logger.info("Embedding model loaded successfully.")
_DATA_ROOT = str(Path(__file__).parent) + "/../../../data"


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
  datas = ["nju_se_teacher.json", "red_and_black_table.json", "course_list.json"]
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
def create_courses_collection():
  mc = MilvusClient(uri=MILVUS_URI)
  create_course_collection(mc, COURSES_COLLECTION_NAME, embedding_model)


@app.command()
def insert_courses():
  mc = MilvusClient(uri=MILVUS_URI)
  if mc.has_collection(COURSES_COLLECTION_NAME):
    mc.drop_collection(COURSES_COLLECTION_NAME)
  create_course_collection(mc, COURSES_COLLECTION_NAME, embedding_model)
  courses_path = "course_list.json"
  logger.info("Starting to insert courses into Milvus")
  data_path = os.path.join(_DATA_ROOT, courses_path)
  with open(data_path, "r", encoding="utf-8") as f:
    courses = json.load(f)
  for course in tqdm(courses):
    data = {}
    nil = False
    for key, value in course.items():
      if value is None or (type(value) == list and len(value) == 0):
        nil = True
        break
      # print(type(value))
      if type(value) == str or type(value) == list:
        if len(value) < 65535:
          data[key] = value
        else:
          data[key] = value[:65535]
      else:
        data[key] = value
    if nil:
      continue
    data_str = json.dumps(data)
    try:
      mc.insert(
        collection_name=COURSES_COLLECTION_NAME,
        data={
          "embedding": embedding_model.encode(data_str),
          "sparse_embedding": sparse_embedding_model([data_str])["sparse"],
          "course_name": data.get("course_name", ""),
          "course_number": data.get("course_number", ""),
          "teacher_name": data.get("teacher_name", ""),
          "department_name": data.get("department_name", ""),
          "campus": data.get("campus", ""),
          "reference_book": data.get("reference_book", ""),
          "teaching_class_id": data.get("teaching_class_id", ""),
          "hours": data.get("hours", 0),
          "school_term": data.get("school_term", ""),
          "time_place": data.get("time_place", [""])[0],
          "teaching_purpose": data.get("teaching_purpose", ""),
          "summary": data.get("summary", ""),
          "grades": data.get("grades", []),
        },
      )
    except Exception as e:
      print(e)
      print(data.get("summary", ""))
      print(type(data.get("summary", "")))
  logger.info("Finished inserting courses into Milvus")


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


@app.command()
def select():
  client = MilvusClient(uri="http://localhost:19530")

  results = client.query(collection_name=COLLECTION_NAME, limit=10, output_fields=["*"])

  for item in results:
    print(item)


if __name__ == "__main__":
  app()
