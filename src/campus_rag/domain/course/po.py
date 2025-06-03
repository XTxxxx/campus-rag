from pydantic import BaseModel


class TimeItem(BaseModel):
  weekday: int
  start: int
  end: int

  def __str__(self) -> str:
    """生成中文描述字符串，包含星期几、开始时间和结束时间。

    Returns:
        str: 描述字符串，格式为 "周[一二三四五六日]，几点到几点"。
    """
    weekday_map = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
    return f"周{weekday_map.get(self.weekday)}，{self.start + 7}点到{self.end + 7}点"


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
