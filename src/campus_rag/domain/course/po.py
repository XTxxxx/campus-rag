from pydantic import BaseModel


class TimeItem(BaseModel):
  weekday: int
  start: int
  end: int


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


class FilterArgs(BaseModel):
  filter: CourseFilter
  start_idx: int
  size: int


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
