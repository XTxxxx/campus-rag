from pydantic import BaseModel
from typing import Any
from campus_rag.domain.course.po import CourseFilter


class ContentsRequest(BaseModel):
  collection_name: str
  page_id: int
  page_size: int


class TopKQueryModel(BaseModel):
  query: str
  collection_name: str
  top_k: int


class TopKQueryModelWithFilter(BaseModel):
  course_filter: CourseFilter
  query: str
  collection_name: str
  top_k: int


class UploadKnowledge(BaseModel):
  # user(admin) upload knowledge style
  collection_name: str
  knowledge: list[dict[str, Any]]
  chunk_keys: list[str]  # use which keys to build chunk
  max_value_size: int  # a key-value when put in chunk, max value size will be used
  meta_field: bool  # if create a meta field


class ModifyChunk(BaseModel):
  collection_name: str
  chunk_id: int
  chunk: str  # new chunk content
