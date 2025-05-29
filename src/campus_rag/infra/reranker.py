"""
This model wraps the reranking models and provides a common interface for them.
The default reranker is BgeV2M3Reranker, which is a cross-encoder model.
It's performance is better, tested in my another project.
"""

from abc import abstractmethod
from typing import List

import requests
from FlagEmbedding import FlagReranker, LayerWiseFlagLLMReranker
from sentence_transformers import CrossEncoder
from campus_rag.utils.chunk_ops import construct_embedding_key


class ModelReranker:
  @abstractmethod
  def rerank(self, query: str, results: List[dict]) -> List[dict]:
    """
    Rerank the results based on the query, according to scroes computed by the cross-encoder

    Args:
      query: Query string
      results: Results of retrieval
    Returns:
      sorted lists of results with scores
    """
    pass

  @abstractmethod
  def get_name(self):
    """
    Get the name of the reranker

    Returns: Name of the reranker
    """
    pass


class BgeV2M3Reranker(ModelReranker):
  def __init__(self):
    self.reranker_name = "BAAI/bge-reranker-v2-m3"
    self.reranker = FlagReranker(
      self.reranker_name, use_fp16=True, trust_remote_code=True
    )

  def rerank(self, query: str, results: List[dict]) -> List[dict]:
    inputs = [[query, construct_embedding_key(res["entity"])] for res in results]
    scores = self.reranker.compute_score(inputs)
    for i in range(len(results)):
      results[i]["score"] = scores[i]
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results

  def get_name(self):
    return self.reranker_name


class JinaReranker(ModelReranker):
  def __init__(self):
    self.reranker_name = "jinaai/jina-reranker-v2-base-multilingual"
    self.url = "http://118.195.161.49:27982/rerank/"

  def rerank(self, query: str, results: List[str]) -> List[dict]:
    for res in results:
      res["embedding_key"] = construct_embedding_key(res["entity"])
    data = {
      "query": query,
      "passages": list([res["embedding_key"] for res in results]),
    }
    response = requests.post(self.url, json=data)
    while response.status_code != 200:
      response = requests.post(self.url, json=data)
    sorted_pairs = response.json()["reranked"]
    sorted_results = []
    for pair in sorted_pairs:
      for i in range(len(results)):
        if results[i]["embedding_key"] == pair[0]:
          results[i]["score"] = pair[1]
          sorted_results.append(results[i])
          break
    return sorted_results

  def get_name(self):
    return self.reranker_name


class JinaRerankerLocal(ModelReranker):
  def __init__(self):
    self.model = CrossEncoder(
      "jinaai/jina-reranker-v2-base-multilingual",
      automodel_args={"torch_dtype": "auto"},
      trust_remote_code=True,
    )

  def get_name(self):
    return "jinaai/jina-reranker-v2-base-multilingual"

  def rerank(self, query: str, results: List[str]) -> List[dict]:
    inputs = [[query, construct_embedding_key(res["entity"])] for res in results]
    scores = self.model.predict(inputs, convert_to_tensor=True).tolist()
    for i in range(len(results)):
      results[i]["score"] = scores[i]
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results


reranker = BgeV2M3Reranker()
