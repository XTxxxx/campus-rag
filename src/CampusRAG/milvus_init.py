"""
This script is used to create a Milvus collection and insert data into it.
Datas are stored in the `data` folder (in json format).

Usage:
- Start Milvus server:
  `cd milvus-standalone`
  `docker compuse up -d`
- To create a collection and insert data:
  `python milvus_init.py all`

TODO: add more collections(maybe not necessary), insert data
"""
from pymilvus import DataType, MilvusClient
from sentence_transformers import SentenceTransformer
from milvus_model.hybrid import BGEM3EmbeddingFunction
import typer

app = typer.Typer()


_COLLECTION_NAME = ""
_MAX_LENGTH = 65535
_MILVUS_URI = "http://localhost:20530"
_embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
_sparse_embedding_model = BGEM3EmbeddingFunction(device="cuda:0")
_DATA_ROOT = "./data"


def create_collections(mc: MilvusClient):
  if mc.has_collection(_COLLECTION_NAME):
    mc.drop_collection(_COLLECTION_NAME)
    print(f"Successfully dropped collection {_COLLECTION_NAME}")
  schema = MilvusClient.create_schema(
    auto_id=True,
    enable_dynamic_field=True,
  )
  schema.add_field("id", DataType.INT64, is_primary=True)
  schema.add_field(
    "embedding",
    DataType.FLOAT_VECTOR,
    dim=_embedding_model.get_sentence_embedding_dimension(),
  )
  # Refer to https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-enrichment-phase for details
  # sparse embedding: sparse vector used for keyword search
  schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
  schema.add_field("source", DataType.VARCHAR, max_length=_MAX_LENGTH)
  # source: where the chunk comes from, used for routing
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
    collection_name=_COLLECTION_NAME, schema=schema, index_params=index_params
  )
  print(f"Successfully created collection {_COLLECTION_NAME}")

def insert_data(mc: MilvusClient):
  # TODO: insert data (from ./data) into Milvus
  pass


@app.command()
def all():
  mc = MilvusClient(uri=_MILVUS_URI)
  create_collections(mc)
  insert_data(mc)

if __name__ == "__main__":
  app()