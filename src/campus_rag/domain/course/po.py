from pydantic import BaseModel


class ScheduleItem(BaseModel):
  weekday: int
  start_ind: int
  length: int
  position: int


class Course(BaseModel):
  id: str  # course id in nju
  name: str
  teacher: list[str]
  credits: int
  campus: str
  schedule: list[ScheduleItem]
  description: str


class Plan(BaseModel):
  id: str
  description: str
  courses: list[Course]
