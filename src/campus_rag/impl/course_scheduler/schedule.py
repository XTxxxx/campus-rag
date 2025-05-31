from campus_rag.domain.course.po import CourseFilter
from campus_rag.domain.course.vo import CourseView, PlanView
from campus_rag.constants.course import (
  MAX_COURSES_PER_FILTER,
  FILTER_LIMIT,
  OUTPUT_JSON,
)
from campus_rag.utils.logging_config import setup_logger
from campus_rag.utils.llm import llm_chat_async, parse_as_json
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


def search_course_from_list(
  course_list: list[CourseView], target_name: str
) -> CourseView | None:
  """Search for a course by its course number in a list of courses."""
  for course in course_list:
    if course.name == target_name:
      return course
  return None


async def generate_plan(
  target_courses: list[CourseView], constraint: str
) -> list[PlanView]:
  """Generate a course plan based on the target courses and user constraints.
  This function uses an LLM to generate a plan description and select courses
  based on the provided constraints.

  Args:
      target_courses (list[CourseView]): List of available courses to choose from.
      constraint (str): User constraint for course selection, such as "no morning classes" or "no back-to-back classes".

  Returns:
      PlanView: A generated course plan containing a description and selected courses.
  """
  prompt = [
    {
      "role": "system",
      "content": "你是一个智能选课规划助手，负责推荐选课计划给用户",
    },
    {
      "role": "user",
      "content": f"""##INSTRUCT##
根据用户输入的课程列表和约束条件，生成1-3个选课计划。不同课之间需要**尽可能**满足约束条件，并且时间不能有冲突。
对每个计划，你需要输出详细的解释，并且每个计划应该有差异，这几个计划应该按照对用户约束条件的满足度进行排序。
##COURSES##
{" ".join(str(course) for course in target_courses)}
##CONSTRAINT##
{constraint}
##OUTPUT##
你的输出是一个json数组，最外层数组中的每一个元素是一个选课计划
{OUTPUT_JSON}
注意，输出是json格式，避免任何无关输出
""",
    },
  ]
  response = await llm_chat_async(prompt)
  json_response = parse_as_json(response)
  plan_list = []
  for json_plan in json_response:
    plan_list.append(
      PlanView(
        description=json_plan.get("description", ""),
        courses=[
          search_course_from_list(target_courses, course["name"])
          for course in json_plan.get("courses", [])
        ],
      )
    )

  return plan_list


async def generate_schedule(
  existing_courses: list[CourseView], filter_list: list[CourseFilter], constraint: str
) -> list[PlanView]:
  """Generate 3 course plans based on the provided courses and preferences.
  First get available courses: the union of courses filtered by each filter in filter_list.
  At the same time, use vector search to find courses that match the preferences, top (FILTER_LIMIT)50 for each filter.
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
  return await generate_plan(target_courses, constraint)
