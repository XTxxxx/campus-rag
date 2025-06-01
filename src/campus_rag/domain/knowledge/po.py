from pydantic import BaseModel
from campus_rag.domain.course.po import CourseFilter


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
  knowledge: list[dict[str]]
  chunk_keys: list[str]  # use which keys to build chunk
  max_value_size: int  # a key-value when put in chunk, max value size will be used
  meta_field: bool  # if create a meta field


class ModifyChunk(BaseModel):
  collection_name: str
  chunk_id: int
  chunk: str  # new chunk content
