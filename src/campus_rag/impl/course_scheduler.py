import campus_rag.utils.milvus_ops as milvus_op
from campus_rag.constants.milvus import COURSES_COLLECTION_NAME
from pydantic import BaseModel


class CourseFilter(BaseModel):
  """Model for filtering courses."""

  course_name: list[str] | None = None
  course_number: list[str] | None = None
  type: list[str] | None = None
  department: list[str] | None = None
  weekday: list[int] | None = None
  campus: list[str] | None = None
  grade: list[int] | None = None
  credit: list[int] | None = (
    None  # Array of 2 integers representing the range of credits (e.g., [2, 4] for 2 to 4 credits)
  )
  preference: str | None = None


class CoursePlan(BaseModel):
  """Model for a course plan."""

  course_name: str
  course_number: str
  type: str
  department_name: str
  weekday: int
  campus: str
  grade: int
  credit: float


def list_departments() -> list[str]:
  """Returns a list of all departments."""
  return list(
    set(milvus_op.select_diy(COURSES_COLLECTION_NAME, None, ["department_name"]))
  )


def list_campuses() -> list[str]:
  """Returns a list of all campuses."""
  return list(set(milvus_op.select_diy(COURSES_COLLECTION_NAME, None, ["campus"])))


def list_grades() -> list[int]:
  """Returns a list of all grades."""
  grades = milvus_op.select_diy(COURSES_COLLECTION_NAME, None, ["grade"])
  grade_set = set()
  for grade in grades:
    if grade["grade"] not in grade_set:
      grade_set.add(grade["grade"])
  return sorted(list(grade_set))


def list_types() -> list[str]:
  """Returns a list of all course types."""
  return list(set(milvus_op.select_diy(COURSES_COLLECTION_NAME, None, ["type"])))


def filter_courses(filter: CourseFilter) -> list[dict]:
  """Filters courses based on the provided filter criteria."""
  query = {}

  if filter.course_name:
    query["course_name"] = {"$in": filter.course_name}
  if filter.course_number:
    query["course_number"] = {"$in": filter.course_number}
  if filter.type:
    query["type"] = {"$in": filter.type}
  if filter.department:
    query["department_name"] = {"$in": filter.department}
  if filter.weekday:
    query["weekday"] = {"$in": filter.weekday}
  if filter.campus:
    query["campus"] = {"$in": filter.campus}
  if filter.grade:
    query["grade"] = {"$in": filter.grade}
  if filter.credit:
    query["credit"] = {"$gte": min(filter.credit), "$lte": max(filter.credit)}

  return milvus_op.select_diy(COURSES_COLLECTION_NAME, query, ["*"])
