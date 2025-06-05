"""
Basic operators
Milvus supports several basic operators for filtering data:

Comparison Operators: ==, !=, >, <, >=, and <= allow filtering based on numeric or text fields.

Range Filters: IN and LIKE help match specific value ranges or sets.

Arithmetic Operators: +, -, *, /, %, and ** are used for calculations involving numeric fields.

Logical Operators: AND, OR, and NOT combine multiple conditions into complex expressions.
"""

from campus_rag.constants.course import COURSES_MAX
from campus_rag.constants.milvus import COLLECTION_NAME
from campus_rag.domain.course.po import CourseFilter, FilterArgs, TimeItem
from campus_rag.domain.course.vo import CourseView, FilterResult
from campus_rag.domain.rag.po import SearchConfig
from campus_rag.infra.milvus.hybrid_retrieve import HybridRetriever
from campus_rag.infra.milvus.init import campus_rag_mc
import logging

logger = logging.getLogger(__name__)


def get_free_time(courses: list[CourseView]) -> list[TimeItem]:
  """Get free time according to existing courses.
  Args:
    courses: List of courses, free time should not conflict with these courses.
  Returns:
    List of free time slots, should be as long as possible (but in one day).
  """
  pass


def time_expr(freetime_list: list[TimeItem]) -> str:
  """Generate a milvus filter expression for free time slots, time path: meta["time_place"], whose structure is:
  "time_place": [
            {
                "time": {
                    "weeks": "1-7周(单)",
                    "day_in_week": 5,
                    "begin_at": 3,
                    "week_binary": "101010100000000000000000000000",
                    "end_at": 4
                },
                "place": "仙Ⅱ-215"
            },
            {
                "time": {
                    "weeks": "1-8周",
                    "day_in_week": 4,
                    "begin_at": 3,
                    "week_binary": "111111110000000000000000000000",
                    "end_at": 4
                },
                "place": "仙Ⅱ-215"
            },
            {
                "time": {
                    "weeks": "9-16周",
                    "day_in_week": 4,
                    "begin_at": 3,
                    "week_binary": "000000001111111100000000000000",
                    "end_at": 4
                },
                "place": "仙Ⅱ-215"
            },
            {
                "time": {
                    "weeks": "9-15周(单)",
                    "day_in_week": 5,
                    "begin_at": 3,
                    "week_binary": "000000001010101000000000000000",
                    "end_at": 4
                },
                "place": "仙Ⅱ-215"
            }
        ],
    Dont consider week for now, just use day_in_week, begin_at, end_at to filter.
    The target entity's time should be within the free time slots.
  Args:
    freetime_list: List of TimeItem objects
  Returns:
    milvus filter expr
  """
  if not freetime_list:
    return ""

  time_conditions = []
  for free_time in freetime_list:
    # For each free time slot, find courses that fit within it
    condition = (
      f'(time_place["time"]["day_in_week"] == {free_time.weekday} AND '
      f'time_place["time"]["begin_at"] >= {free_time.start_ind} AND '
      f'time_place["time"]["end_at"] <= {free_time.start_ind + free_time.length})'
    )
    time_conditions.append(condition)

  return f"( {' OR '.join(time_conditions)} )"


def name_expr(name: list[str]) -> str:
  """Generate a milvus filter expression for course name, name path: meta["course_name"].
  The target entity's name should be substring of some string in the list.  (fuzzy)
  Args:
    name: Course name
  Returns:
    milvus filter expr
  """
  if not name:
    return ""

  conditions = []
  for course_name in name:
    conditions.append(f'meta["course_name"] like "%{course_name}%"')

  return f"( {' OR '.join(conditions)} )"


def course_number_expr(course_number: list[str]) -> str:
  """Generate a milvus filter expression for course number, number path: meta["course_number"].
  The target entity's course number should be substring of some string in the list. (fuzzy)
  Args:
    course_number: Course number
  Returns:
    milvus filter expr
  """
  if not course_number:
    return ""

  conditions = []
  for number in course_number:
    conditions.append(f'meta["course_number"] like "%{number}%"')

  return f"( {' OR '.join(conditions)} )"


def type_expr(course_type: list[str]) -> str:
  """Generate a milvus filter expression for course type, type path: meta["course_type"].
  The target entity's type should appear in the list. (exact)
  Args:
    course_type: Course type
  Returns:
    milvus filter expr
  """
  if not course_type:
    return ""

  quoted_types = [f'"{t}"' for t in course_type]
  return f'(meta["course_type"] in [{", ".join(quoted_types)}])'


def department_expr(department: list[str]) -> str:
  """Generate a milvus filter expression for department, department path: meta["department_name"].
  The target entity's department should appear in the list. (exact)
  Args:
    department: Department name
  Returns:
    milvus filter expr
  """
  if not department:
    return ""

  quoted_departments = [f'"{d}"' for d in department]
  return f'(meta["department_name"] in [{", ".join(quoted_departments)}])'


def weekday_sub_expr(weekday: list[int]) -> str:
  """Generate a milvus filter expression for weekday, weekday path: meta["weekday"].
  The target entity's weekdays should be within the list. Data structure see docstring of time_expr.
  In the database, dow 0 standards for free time, so we should always include it.
  Args:
    weekday: Weekday
  Returns:
    milvus filter expr
  """
  if not weekday:
    return ""

  weekday_list = list(set(weekday))
  return f'(ARRAY_CONTAINS_ANY(meta["dows"], {str(weekday_list + [0])}))'


def campus_expr(campus: list[str]) -> str:
  """Generate a milvus filter expression for campus, campus path: meta["campus"].
  The target entity's campus should appear in the list. (exact)
  Args:
    campus: Campus name
  Returns:
    milvus filter expr
  """
  if not campus:
    return ""

  quoted_campuses = [f'"{c}"' for c in campus]
  return f'(meta["campus"] in [{", ".join(quoted_campuses)}])'


def grade_expr(grade: list[int]) -> str:
  """Generate a milvus filter expression for grade, grade path: meta["grade"].
  The target entity's grade should appear in the list. (exact)
  Args:
    grade: Grade
  Returns:
    milvus filter expr
  """
  if not grade:
    return ""

  return f'(ARRAY_CONTAINS_ANY(meta["grades"], {str(grade)}))'


def credit_expr(credit: list[int]) -> str:
  """Generate a milvus filter expression for credit, credit path: meta["credit"].
  The target entity's credit should be in the range of the list. (range)
  Args:
    credit: Credit range of 2 integers, e.g., [2, 4] for 2 to 4 credits
  Returns:
    milvus filter expr
  """
  if not credit or len(credit) != 2:
    return ""

  min_credit, max_credit = credit
  return f'(meta["credit"] >= {min_credit} AND meta["credit"] <= {max_credit})'


def gen_filter_expr(filter: CourseFilter) -> str:
  """Generates a filter expression based on the provided CourseFilter."""
  exprs = []

  # Define filter mappings
  filter_mappings = [
    (filter.course_name, name_expr),
    (filter.course_number, course_number_expr),
    (filter.type, type_expr),
    (filter.department, department_expr),
    (filter.weekday, weekday_sub_expr),
    (filter.campus, campus_expr),
    (filter.grade, grade_expr),
    (filter.credit, credit_expr),
  ]

  # Apply filters
  for filter_value, expr_func in filter_mappings:
    if filter_value:
      expr = expr_func(filter_value)
      if expr:
        exprs.append(expr)

  # Combine all expressions with AND
  if exprs:
    exprs = "AND ".join(exprs)
    return 'source == "course" AND' + exprs


filter_retriever = HybridRetriever(campus_rag_mc, COLLECTION_NAME)


def cal_total(filter_expr: str) -> int:
  """Calculates the total number of courses matching the filter expression."""
  if not filter_expr:
    return 0

  res = campus_rag_mc.query(
    COLLECTION_NAME,
    filter_expr,
    ["id"],
    limit=COURSES_MAX,
  )
  return len(res)


async def filter_courses(
  course_filter: CourseFilter, limit: int = COURSES_MAX, offset: int = 0
) -> FilterResult:
  expr = gen_filter_expr(course_filter)
  logger.debug(f"Generated filter expression: {expr}")
  total = cal_total(expr)

  if course_filter.preference:  # Perform hybrid search if preference is set
    logger.debug(f"Using preference for filter: {course_filter.preference}")
    search_config = SearchConfig(
      filter_expr=expr,
      limit=limit,
      offset=offset,
      output_fields=["id", "meta", "distance"],
    )
    search_res = await filter_retriever.retrieve(
      course_filter.preference, config=search_config
    )
    logger.debug(f"Hybrid search results count: {len(search_res)}")
    course_view_list = [CourseView.from_filter_result(data) for data in search_res]
    return FilterResult(
      filtered_courses=course_view_list,
      total=total,
    )
  search_results = campus_rag_mc.query(
    COLLECTION_NAME,
    expr,
    ["id", "meta"],
    limit=limit,
    offset=offset,
  )
  logger.debug(f"Search results count: {len(search_results)}")
  course_view_list = [CourseView.from_filter_result(data) for data in search_results]
  return FilterResult(filtered_courses=course_view_list, total=total)


async def filter_courses_pagination(filter_arg: FilterArgs) -> FilterResult:
  """Filters courses based on the provided filter criteria."""
  return await filter_courses(
    course_filter=filter_arg.filter,
    limit=filter_arg.size,
    offset=filter_arg.start_idx,
  )
