import uuid
import json
import os

files = [
  "course_list.json",
  "red_and_black_table.json",
  "student_manual.json",
  "nju_se_teacher.json",
]


def find_target_chunk(idx):
  with open("data/course_list.json") as f:
    data = json.load(f)
    return data[idx - 1]["id"]


def substitute_id():
  with open("data/test-data/question_course.json", "r") as f:
    data = json.load(f)
  for item in data:
    expected_chunks = []
    for id in item["expected_chunks"]:
      chunk = find_target_chunk(id)
      expected_chunks.append(chunk)
    item["expected_chunks"] = expected_chunks
  with open("data/test-data/question_course.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


def alloc_id():
  for file_name in files:
    with open(os.path.join("data", file_name), "r", encoding="utf-8") as f:
      data = json.load(f)

    for item in data:
      item["id"] = str(uuid.uuid4())

    with open(os.path.join("data", file_name), "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

  print("ID allocation completed.")
