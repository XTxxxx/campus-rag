import json

with open("./data/nju_se_teacher.json", "r", encoding="utf-8") as f:
  data = json.load(f)
for item in data:
  item["cleaned_chunk"] = ""
  item["source"] = "软院官网"
  item["chunk"] = item["chunk"].replace(" ", "")
  item["chunk"] = item["chunk"][:4096]
with open("./data/nju_se_teacher.json", "w", encoding="utf-8") as f:
  json.dump(data, f, ensure_ascii=False, indent=2)
