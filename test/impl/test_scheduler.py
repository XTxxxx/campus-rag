from campus_rag.data_pipeline import course_type
from campus_rag.impl.course_scheduler.schedule import (
  get_target_courses,
  generate_schedule,
)

from campus_rag.domain.course.po import CourseFilter, TimeItem
from campus_rag.domain.course.vo import CourseView
from campus_rag.utils.logging_config import setup_logger
import pytest

logger = setup_logger()


@pytest.mark.asyncio
async def test_get_target_courses():
  """
  Test the get_target_courses function.
  This is a simple test that checks if the function returns a non-empty list.
  """
  # This is desgined
  filter1 = CourseFilter(
    campus=["仙林校区"],
    preference="我喜欢逻辑学和经典物理",
  )
  existing_course = CourseView(
    id=123,
    course_number="MATH101",
    name="数学基础",
    teacher=["张老师"],
    credit=3,
    department="数学系",
    campus="仙林校区",
    time=[TimeItem(weekday=5, start=1, end=4)],
  )

  courses_res1 = await get_target_courses([], [filter1])
  for i, course in enumerate(courses_res1):
    logger.info(f"course {i}: {course}")
  courses_res2 = await get_target_courses([existing_course], [filter1])
  for i, course in enumerate(courses_res2):
    logger.info(f"course {i}: {course}")
  assert courses_res1[0] != courses_res2[0]


@pytest.mark.asyncio
async def test_plan():
  """
  Test the get_target_courses function.
  This is a simple test that checks if the function returns a non-empty list.
  """
  # This is desgined
  filter1 = CourseFilter(
    type=["公共体育课"],
    preference="球类课程",
  )
  existing_course = CourseView(
    id=123,
    course_number="MATH101",
    name="数学基础",
    teacher=["张老师"],
    credit=3,
    department="数学系",
    campus="仙林校区",
    time=[TimeItem(weekday=5, start=1, end=4)],
  )
  constraint = "避免早八课，不要在周三有课"

  plan = await generate_schedule(
    existing_courses=[existing_course],
    filter_list=[filter1],
    constraint=constraint,
  )

  logger.info(f"Generated plan: {plan}")
