import campus_rag.infra.milvus.course_ops as course_searcher
from campus_rag.constants.milvus import COLLECTION_NAME


def list_something(_key: str):
  """Returns a list of unique values for a given key in the courses collection."""
  data_list = course_searcher.select_diy(
    COLLECTION_NAME, 'source == "course"', ["meta"], limit=10000
  )
  value_set = set([data["meta"][_key] for data in data_list if _key in data["meta"]])
  return sorted(list(value_set))


def list_departments() -> list[str]:
  """Returns a list of all departments."""
  return list_something("department_name")


def list_campuses() -> list[str]:
  """Returns a list of all campuses."""
  return list_something("campus")


def list_grades() -> list[int]:
  """Returns a list of all grades."""
  data_list = course_searcher.select_diy(
    COLLECTION_NAME, 'source == "course"', ["meta"], limit=10000
  )
  grades = [data["meta"]["grades"] for data in data_list if "grades" in data["meta"]]
  grade_set = set()
  for grade_list in grades:
    for grade in grade_list:
      if grade not in grade_set:
        grade_set.add(grade)
  return sorted(list(grade_set))


def list_types() -> list[str]:
  return list_something("course_type")
