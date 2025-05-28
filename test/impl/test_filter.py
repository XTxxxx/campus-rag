from logging import Filter
from campus_rag.impl.course_scheduler.filter import filter_courses
from campus_rag.domain.course.po import CourseFilter, FilterArgs
from campus_rag.utils.logging_config import setup_logger
import pytest

logger = setup_logger()


@pytest.mark.asyncio
async def test_filter_by_course_name():
  """Test filtering courses by course name."""
  logger.info("Starting test: Filter by course name")

  filter_args = FilterArgs(
    filter=CourseFilter(
      course_name=["数学", "物理"],
    ),
    start_idx=0,
    size=10,
  )

  filter_res = await filter_courses(filter_args)
  courses = filter_res.filtered_courses
  total = filter_res.total
  logger.info(f"Results count: {len(courses)} out of {total} total courses")
  if courses:
    logger.info(f"Example result: {courses[0]}")


@pytest.mark.asyncio
async def test_filter_by_weekday():
  """Test filtering courses by weekday."""
  logger.info("Starting test: Filter by weekday")

  filter_args = FilterArgs(
    filter=CourseFilter(
      weekday=[1, 2, 5],
    ),
    start_idx=0,
    size=10,
  )

  filter_res = await filter_courses(filter_args)
  courses = filter_res.filtered_courses
  logger.info(f"Results count: {len(courses)} out of {filter_res.total} total courses")
  if courses:
    logger.info(f"Example result: {courses[0]}")


@pytest.mark.asyncio
async def test_filter_multiple_criteria():
  """Test filtering courses with multiple criteria."""
  logger.info("Starting test: Multiple filters")

  filter_args = FilterArgs(
    filter=CourseFilter(
      course_name=["操作", "算法", "分析"],
      department=["计算机学院"],
      campus=["仙林校区"],
      grade=[2022],
      credit=[2, 4],
    ),
    start_idx=0,
    size=10,
  )

  filter_res = await filter_courses(filter_args)
  courses = filter_res.filtered_courses

  logger.info(f"Results count: {len(courses)} out of {filter_res.total} total courses")
  if courses:
    logger.info(f"Example result: {courses[0]}")
  else:
    logger.info("No results found for multiple criteria")


@pytest.mark.asyncio
async def test_filter_empty():
  """Test filtering courses with empty filter."""
  logger.info("Starting test: Empty filter")
  filter_args = FilterArgs(
    filter=CourseFilter(),
    start_idx=0,
    size=10,
  )

  filter_res = await filter_courses(filter_args)
  courses = filter_res.filtered_courses
  # Assert Length should in [0, 10]
  assert len(courses) <= 10, "Result length is out of expected range"

  if courses:
    logger.info(f"Example result: {courses[0]}")


@pytest.mark.asyncio
async def test_pagination():
  """Test pagination functionality.
  Search top 20 and at once then search [0, 10) and [10, 20). Assert the results are the same.
  """
  logger.info("Starting test: Pagination")

  # First, filter top 20 courses
  all_results = await filter_courses(
    FilterArgs(filter=CourseFilter(), start_idx=0, size=20)
  )
  all_courses = all_results.filtered_courses
  logger.info(f"Total results count: {len(all_courses)}")

  # Paginate results
  first_page_res = await filter_courses(
    FilterArgs(filter=CourseFilter(), start_idx=0, size=10)
  )
  first_page = first_page_res.filtered_courses
  second_page_res = await filter_courses(
    FilterArgs(filter=CourseFilter(), start_idx=10, size=10)
  )
  second_page = second_page_res.filtered_courses

  # assert content of first and second page
  assert all_courses[:10] == first_page, "First page results do not match"
  assert all_courses[10:20] == second_page, "Second page results do not match"

  logger.info("Pagination test passed")


@pytest.mark.asyncio
async def test_preference_filter():
  """Test filtering with preference."""
  logger.info("Starting test: Preference filter")

  filter_args = FilterArgs(
    filter=CourseFilter(
      grade=[2022],
      preference="我想选一门数学课",
    ),
    start_idx=0,
    size=10,
  )

  filter_res = await filter_courses(filter_args)
  courses = filter_res.filtered_courses
  logger.info(f"Results count: {len(courses)} out of {filter_res.total} total courses")
  if courses:
    logger.info(f"Example result: {courses[0]}")
  else:
    logger.info("No results found for preference filter")


@pytest.mark.asyncio
async def test_preference_pagination():
  """Test preference filter with pagination.
  The inconsistency of the results is introduced by ANN search, so we need
  """
  logger.info("Starting test: Preference filter with pagination")

  # First, filter top 20 courses with preference
  all_results = await filter_courses(
    FilterArgs(filter=CourseFilter(preference="我想选一门数学课"), start_idx=0, size=20)
  )
  all_courses = all_results.filtered_courses
  logger.info(f"Total results count: {len(all_courses)}")

  # Paginate results
  first_page_res = await filter_courses(
    FilterArgs(filter=CourseFilter(preference="我想选一门数学课"), start_idx=0, size=10)
  )
  first_page = first_page_res.filtered_courses
  second_page_res = await filter_courses(
    FilterArgs(
      filter=CourseFilter(preference="我想选一门数学课"), start_idx=10, size=10
    )
  )
  second_page = second_page_res.filtered_courses

  # assert content of first and second page
  assert all_courses[:10] == first_page, "First page results do not match"
  assert all_courses[10:20] == second_page, "Second page results do not match"

  logger.info("Preference pagination test passed")
