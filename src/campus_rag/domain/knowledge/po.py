from pydantic import BaseModel
from src.campus_rag.domain.course.po import CourseFilter


class TopKQueryModel(BaseModel):
  query: str
  collection_name: str
  top_k: int


class TopKQueryModelWithFilter(BaseModel):
  course_filter: CourseFilter
  query: str
  collection_name: str
  top_k: int
