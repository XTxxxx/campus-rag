import logging
from sentence_transformers import SentenceTransformer
from milvus_model.hybrid import BGEM3EmbeddingFunction

logger = logging.getLogger(__name__)
logger.info("Loading embedding model...")
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
sparse_embedding_model = BGEM3EmbeddingFunction(device="cuda:0")
logger.info("Embedding model loaded successfully.")
