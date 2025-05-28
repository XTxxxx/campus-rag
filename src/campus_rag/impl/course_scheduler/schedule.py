from campus_rag.domain.course.po import CourseFilter
from campus_rag.domain.course.vo import CourseView, PlanView
from campus_rag.constants.course import MAX_COURSES_PER_FILTER, FILTER_LIMIT
from campus_rag.utils.logging_config import setup_logger
from .filter import filter_courses

logger = setup_logger()


def is_conflicting(course: CourseView, existing_course: CourseView) -> bool:
  """Check if two courses conflict based on course number or time place.
  Iter thourgh the time items of both courses to check for conflicts.
  """
  if course.course_number == existing_course.course_number:
    return True
  for time_item in course.time:
    for existing_time_item in existing_course.time:
      if (
        time_item.weekday == existing_time_item.weekday
        and time_item.start <= existing_time_item.end
        and time_item.end >= existing_time_item.start
      ):
        return True
  return False


def filter_conflict_courses(
  courses: list[CourseView], existing_courses: list[CourseView]
) -> list[CourseView]:
  """Filter out courses that conflict with existing courses."""
  courses = list(
    filter(
      lambda course: not any(
        is_conflicting(course, existing_course) for existing_course in existing_courses
      ),
      courses,
    )
  )
  return courses


async def get_target_courses(
  existing_courses: list[CourseView], filter_list: list[CourseFilter]
) -> list[CourseView]:
  courses_list = []
  for filter in filter_list:
    filter_res = await filter_courses(filter, limit=FILTER_LIMIT)
    courses_list.append(filter_res.filtered_courses)
  courses_list = [
    filter_conflict_courses(course_list, existing_courses)
    for course_list in courses_list
  ]
  available_course_ids = set()
  target_course_list = []
  for course_list in courses_list:
    for course in course_list[:MAX_COURSES_PER_FILTER]:
      if course.id not in available_course_ids:
        target_course_list.append(course)
        available_course_ids.add(course.id)
  logger.debug(f"Collected {len(target_course_list)} courses for plan generation")
  return target_course_list


async def generate_schedule(
  existing_courses: list[CourseView], filter_list: list[CourseFilter], constraint: str
) -> list[PlanView]:
  """Generate 3 course plans based on the provided courses and preferences.
  First get available courses: the union of courses filtered by each filter in filter_list.
  At the same time, use vector search to find courses that match the preferences, top 50 for each filter.
  Then exclude courses that conflict with the existing courses.
  Finally, generate 3 plans based on the available courses and preferences.
    The context should be 6(MAX_COURSES_PER_FILTER) courses for each filter.

  Args:
      courses (list[CourseView]): existing courses, used to exclude conflicting courses.
      constraint (str): User constraint for course selection, such as "no morning classes" or "no back-to-back classes".

  Returns:
      list[PlanView]: A list of generated course plans.
  """
  target_courses = await get_target_courses(existing_courses, filter_list)
