from fastapi.routing import APIRouter
from campus_rag.impl.course_scheduler.show_info import (
  list_departments,
  list_campuses,
  list_grades,
  list_types,
)
from campus_rag.impl.course_scheduler.filter import filter_courses
from campus_rag.domain.course.po import CourseFilter, FilterArgs
from campus_rag.domain.course.vo import CourseView, FilterResult, PlanView
from campus_rag.impl.course_scheduler.schedule import generate_schedule

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


@router.post("/course/filter", response_model=FilterResult)
async def get_filtered_courses(filter: FilterArgs) -> FilterResult:
  """Returns a list of filtered courses."""
  return await filter_courses(filter)


@router.post("/course/genplan", response_model=list[CourseView])
async def generate_course_plan(
  current: list[CourseView], filter_list: list[CourseFilter], constraint: str
) -> list[PlanView]:
  """Generates a course plan based on the current course and filter criteria."""
  return await generate_schedule(current, filter_list, constraint)
