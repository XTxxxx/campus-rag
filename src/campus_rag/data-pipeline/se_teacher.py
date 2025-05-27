import json

# 读取 JSON 文件
with open(
  r"D:\codesforpython\rag\data\nju_se_teacher.json", "r", encoding="utf-8"
) as file:
  data = json.load(file)

# 遍历 JSON 数据，提取 chunk 的第一个字段写入 cleaned_chunk
for item in data:
  if "chunk" in item and item["chunk"]:  # 检查 chunk 字段是否存在且不为空
    first_field = (
      item["chunk"].split(",")[0].strip() + " 南京大学" + " 软件学院"
    )  # 提取第一个字段并去除前后空格
    item["cleaned_chunk"] = first_field  # 写入 cleaned_chunk

# 将处理后的数据写回 JSON 文件
with open(
  r"D:\codesforpython\rag\data\nju_se_teacher.json", "w", encoding="utf-8"
) as file:
  json.dump(data, file, ensure_ascii=False, indent=4)

print("cleaned_chunk 字段已成功写入 data_cleaned.json 文件。")
