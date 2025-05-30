import json

red_black = json.load(open("../../../data/red_and_black_table.json", encoding="utf-8"))
courses = json.load(open("../../../data/course_list.json", encoding="utf-8"))


def check(src_teacher_name: str, target_teacher_name: str):
  if not src_teacher_name or not target_teacher_name:
    return False
  return (
    src_teacher_name == target_teacher_name or src_teacher_name in target_teacher_name
  )


for item in red_black:
  for i in range(len(courses)):
    src_teacher_name = item["cleaned_chunk"].split(" ")[-1]
    if src_teacher_name.endswith("等老师"):
      src_teacher_name = src_teacher_name[:-3]
    target_teacher_name = courses[i]["teacher_name"]
    if check(src_teacher_name, target_teacher_name):
      print(src_teacher_name, target_teacher_name)
      # 添加一个新字段
      if "comments" in courses[i].keys():
        courses[i]["comments"].append(item["chunk"])
      else:
        courses[i]["comments"] = [item["chunk"]]
# 写回
json.dump(
  courses,
  open("../../../data/course_list_rb.json", "w", encoding="utf-8"),
  ensure_ascii=False,
  indent=2,
)
