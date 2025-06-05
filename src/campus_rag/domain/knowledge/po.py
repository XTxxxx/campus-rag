from typing import Any
from pydantic import BaseModel


class ContentsRequest(BaseModel):
  collection_name: str
  page_id: int
  page_size: int


class TopKQueryModel(BaseModel):
  query: str
  collection_name: str
  top_k: int


class UploadKnowledge(BaseModel):
  # user(admin) upload knowledge style
  collection_name: str
  knowledge: list[dict[str, Any]]


class ModifyChunk(BaseModel):
  collection_name: str
  chunk_id: int
  chunk: str  # new chunk content
