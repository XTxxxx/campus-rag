from fastapi.routing import APIRouter
from campus_rag.impl.course_scheduler.show_info import (
  list_departments,
  list_campuses,
  list_grades,
  list_types,
)
from campus_rag.impl.course_scheduler.filter import filter_courses
from campus_rag.domain.course.po import CourseFilter
from campus_rag.domain.course.vo import CourseView

router = APIRouter()


@router.get(
  "/course/departments",
  response_model=list[str],
  response_description="List all departments",
)
def get_departments() -> list[str]:
  """Returns a list of all departments."""
  return list_departments()


@router.get(
  "/course/campuses",
  response_model=list[str],
  response_description="List all campuses",
)
def get_campuses() -> list[str]:
  """Returns a list of all campuses."""
  return list_campuses()


@router.get(
  "/course/grades",
  response_model=list[int],
  response_description="List all grades",
)
def get_grades() -> list[int]:
  """Returns a list of all grades."""
  return list_grades()


@router.get(
  "/course/types",
  response_model=list[str],
  response_description="List all course types",
)
def get_types() -> list[str]:
  return list_types()


@router.post("/course/filter", response_model=list[CourseView])
def get_filtered_courses(filter: CourseFilter) -> list[CourseView]:
  """Returns a list of filtered courses."""
  return filter_courses(filter)


@router.post("/course/genplan", response_model=list[CourseView])
def generate_course_plan(current: CourseView, filterlists: list[CourseFilter]):
  """Generates a course plan based on the current course and filter criteria."""
  # This function should implement the logic to generate a course plan
  # based on the current course and the provided filter criteria.
  # For now, it returns an empty list as a placeholder.
  return []  # Placeholder for actual implementation
