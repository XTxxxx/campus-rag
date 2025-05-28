from campus_rag.domain.course.po import CourseFilter
from campus_rag.domain.course.vo import CourseView, PlanView
from .filter import filter_courses


async def generate_schedule(
  courses: list[CourseView], filter_list: list[CourseFilter], constraint: str
) -> list[PlanView]:
  """Generate 3 course plans based on the provided courses and preferences.
  First get available courses: the union of courses filtered by each filter in filter_list.
  At the same time, use vector search to find courses that match the preferences, top 50 for each filter.
  Then exclude courses that conflict with the existing courses.
  Finally, generate 3 plans based on the available courses and preferences.
    The context should be 6 courses for each plan.

  Args:
      courses (list[CourseView]): existing courses, used to exclude conflicting courses.
      constraint (str): User constraint for course selection, such as "no morning classes" or "no back-to-back classes".

  Returns:
      list[PlanView]: A list of generated course plans.
  """
  courses_list = []
  for filter in filter_list:
    filter_res = await filter_courses(filter)
    courses_list.extend(filter_res.filtered_courses)

  pass
