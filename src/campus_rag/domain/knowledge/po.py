from typing import Any
from pydantic import BaseModel


class ContentsRequest(BaseModel):
  sources: list[str]
  page_id: int
  page_size: int


class TopKQueryModel(BaseModel):
  query: str
  sources: list[str]
  top_k: int


class UploadKnowledge(BaseModel):
  # user(admin) upload knowledge style
  sources: list[str]  # maybe a new source
  knowledge: list[dict[str, Any]]


class ModifyRequest(BaseModel):
  request_id: str  # id in collection
  context: str
  chunk: str
  cleaned_chunk: str
