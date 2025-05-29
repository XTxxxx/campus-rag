import json
from campus_rag.data_pipeline.course_crawler import LIST_PATH


def test_required_fields():
  """
  Test that all required fields are present and valid.
  """
  with open(LIST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

  for course in data:
    assert course.get("course_name"), f"Missing course_name in {course}"
    assert course.get("course_number"), f"Missing course_number in {course}"
    assert course.get("department_name"), f"Missing department_name in {course}"
    assert course.get("campus"), f"Missing campus in {course}"
    assert "credit" in course and isinstance(course["credit"], (int, float)), (
      f"Missing or invalid credit in {course}"
    )


def test_time_place_structure():
  """
  Test that time_place has correct structure when present.
  """
  with open(LIST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

  for course in data:
    if "time_place" not in course or not course["time_place"]:
      continue
    for time_place in course["time_place"]:
      assert "time" in time_place, f"Missing time in {course}"
      assert "day_in_week" in time_place["time"], f"Missing day_in_week in {course}"
      assert "begin_at" in time_place["time"], f"Missing begin_at in {course}"
      assert "end_at" in time_place["time"], f"Missing end_at in {course}"
