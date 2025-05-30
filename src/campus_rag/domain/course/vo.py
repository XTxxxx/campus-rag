from unittest.mock import Base
from pydantic import BaseModel, Field
from typing import Optional

from campus_rag.utils.chunk_ops import construct_intro4disp
from .po import TimeItem, CourseFilter


class CourseView(BaseModel):
  """Model for a course view."""

  id: int = Field(..., description="Unique identifier for the course")
  course_number: str = Field(..., description="Course number")
  name: str = Field(..., description="Name of the course")
  teacher: list[str] = Field(..., description="Type of the course (e.g., lecture, lab)")
  credit: float = Field(..., description="Credit hours for the course")
  department: str = Field(..., description="Name of the department offering the course")
  campus: str = Field(..., description="Campus where the course is offered")
  time: list[TimeItem] = Field(
    ...,
    description="Time details of the course including weekday, start time, and duration",
  )
  description: Optional[str] = Field(
    default=None,
    description="Description of the course, including prerequisites and content",
  )
  rednblack: Optional[str] = Field(
    default=None,
    description="Red and Black table representation of the course",
  )
  distance: Optional[float] = Field(
    default=None,
    description="Distance for vector if use preference search, otherwise None",
  )

  def __str__(self) -> str:
    return f"""课程名：{self.name} 课程号：{self.course_number} {self.credit} 学分,
院系和校区: {self.department}, {self.campus} 老师：{self.teacher}
时间: {self.time}
描述: {self.description or "无描述"}
"""

  @classmethod
  def from_filter_result(cls, course: dict) -> "CourseView":
    """Converts a course dictionary to a CourseView."""
    teacher_str = course["meta"].get("teacher_name", "")
    teachers = teacher_str.split(",") if teacher_str else []
    if course["meta"].get("time_place"):
      time_list = [
        TimeItem(
          weekday=tap["time"]["day_in_week"],
          start=tap["time"]["begin_at"],
          end=int(tap["time"]["end_at"]),
        )
        for tap in course["meta"]["time_place"]
      ]

    else:
      time_list = []

    distance = None
    if "distance" in course:
      distance = course["distance"]

    return CourseView(
      id=course["id"],
      course_number=course["meta"]["course_number"],
      name=course["meta"]["course_name"],
      teacher=teachers,
      credit=course["meta"]["credit"],
      department=course["meta"]["department_name"],
      campus=course["meta"]["campus"],
      time=time_list,
      description=construct_intro4disp(course["meta"]),
      rednblack=None,
      distance=distance,
    )


class FilterResult(BaseModel):
  """Model for the result of a course filter operation."""

  total: int = Field(..., description="Total number of courses matching the filter")
  filtered_courses: list[CourseView] = Field(
    ...,
    description="List of CourseView objects representing the filtered courses",
  )


class PlanView(BaseModel):
  """Model for a course plan view."""

  description: str = Field(
    description="Description of the course plan, if available",
  )

  courses: list[CourseView] = Field(
    ...,
    description="List of CourseView objects representing the courses in the plan",
  )


class GeneratePlanRequest(BaseModel):
  current: list[CourseView]
  filter_list: list[CourseFilter]
  constraint: str
