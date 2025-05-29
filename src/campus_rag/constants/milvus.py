from sentence_transformers import SentenceTransformer  # noqa
from milvus_model.hybrid import BGEM3EmbeddingFunction  # noqa

COLLECTION_NAME = "example"
MILVUS_URI = "http://localhost:19530"
COURSES_COLLECTION_NAME = "courses"
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
sparse_embedding_model = BGEM3EmbeddingFunction(device="cuda:0")

INSERT_BATCH_SIZE = 64