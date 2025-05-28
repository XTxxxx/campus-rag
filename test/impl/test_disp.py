from campus_rag.impl.course_scheduler.show_info import (
  list_campuses,
  list_grades,
  list_departments,
  list_types,
)
import campus_rag.infra.milvus.course_ops as course_searcher
from campus_rag.constants.milvus import COURSES_COLLECTION_NAME
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


def test_diy():
  data_list = course_searcher.select_diy(
    COURSES_COLLECTION_NAME, None, ["meta"], limit=10000
  )
  types = set([data["meta"]["course_type"] for data in data_list])
  logger.info(types)


def test_list_types():
  """Test the list of course types."""
  types = list_types()
  assert isinstance(types, list)
  assert len(types) > 0
  logger.info(f"Course types: {types}")


def test_list_departments():
  """Test the list of departments."""
  departments = list_departments()
  assert isinstance(departments, list)
  assert len(departments) > 0
  logger.info(f"Departments: {departments}")


def test_list_campuses():
  """Test the list of campuses."""
  campuses = list_campuses()
  assert isinstance(campuses, list)
  assert len(campuses) > 0
  logger.info(f"Campuses: {campuses}")


def test_list_grades():
  """Test the list of grades."""
  grades = list_grades()
  assert isinstance(grades, list)
  assert len(grades) > 0
  logger.info(f"Grades: {grades}")
