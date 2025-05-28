from campus_rag.impl.course_scheduler.filter import filter_courses
from campus_rag.domain.course.po import CourseFilter
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


def test_filter_by_course_name():
  """Test filtering courses by course name."""
  logger.info("Starting test: Filter by course name")

  filter1 = CourseFilter(
    course_name=["数学", "物理"],
    course_number=None,
    type=None,
    department=None,
    weekday=None,
    campus=None,
    grade=None,
    credit=None,
    start_ind=0,
    size=10,
  )

  result = filter_courses(filter1)
  logger.info(f"Results count: {len(result)}")
  if result:
    logger.info(f"Example result: {result[0]}")

  # if result:
  #   logger.info(f"Sample result keys: {result[0].keys()}")
  # else:
  #   logger.info("No results found")


def test_filter_by_weekday():
  """Test filtering courses by weekday."""
  logger.info("Starting test: Filter by weekday")

  filter2 = CourseFilter(
    course_name=None,
    course_number=None,
    type=None,
    department=None,
    weekday=[1, 2, 5],
    campus=None,
    grade=None,
    credit=None,
    start_ind=0,
    size=10,
  )

  result = filter_courses(filter2)
  logger.info(f"Results count: {len(result)}")
  if result:
    logger.info(f"Example result: {result[0]}")


def test_filter_multiple_criteria():
  """Test filtering courses with multiple criteria."""
  logger.info("Starting test: Multiple filters")

  filter3 = CourseFilter(
    course_name=["操作", "算法", "分析"],
    course_number=None,
    # type=["专业课"],
    department=["计算机学院"],
    # weekday=[1],
    campus=["仙林校区"],
    grade=[2022],
    credit=[2, 4],
    start_ind=0,
    size=10,
  )

  result = filter_courses(filter3)
  logger.info(f"Results count: {len(result)}")
  if result:
    logger.info(f"Example result: {result[0]}")
  else:
    logger.info("No results found for multiple criteria")


def test_filter_empty():
  """Test filtering courses with empty filter."""
  logger.info("Starting test: Empty filter")

  filter4 = CourseFilter(
    course_name=None,
    course_number=None,
    type=None,
    department=None,
    weekday=None,
    campus=None,
    grade=None,
    credit=None,
    start_ind=0,
    size=10,
  )

  result = filter_courses(filter4)
  logger.info(f"Results count: {len(result)}")
  if result:
    logger.info(f"Example result: {result[0]}")


def test_filter_courses():
  """Main test function that runs all individual tests."""
  logger.info("=" * 60)
  logger.info("Starting filter_courses test suite")
  logger.info("=" * 60)

  # Run all tests
  test_filter_by_course_name()
  logger.info("-" * 50)

  test_filter_by_weekday()
  logger.info("-" * 50)

  test_filter_multiple_criteria()
  logger.info("-" * 50)

  test_filter_empty()
  logger.info("-" * 50)

  logger.info("Test suite completed")


if __name__ == "__main__":
  test_filter_courses()
