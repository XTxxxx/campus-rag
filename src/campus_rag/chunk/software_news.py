import json
import re
from keybert import KeyBERT

# 初始化KeyBERT
kw_model = KeyBERT()


# 读取JSON文件
def load_json(file_path):
  with open(file_path, "r", encoding="utf-8") as f:
    return json.load(f)


# 保存JSON文件
def save_json(data, file_path):
  with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# 处理数据
def process_data(chunks):
  for item in chunks:
    # 修复chunk，将\n替换为" "
    item["chunk"] = item["chunk"].replace("\n", " ").strip()

    if "keywords" in item:
      del item["keywords"]

    # 生成关键词，以人物为主，限制为5个
    keywords = kw_model.extract_keywords(item["chunk"], stop_words="english", top_n=5)
    print(keywords)
    item["cleaned_chunk"] = [
      keyword[0] for keyword in keywords if isinstance(keyword[0], str)
    ]
    item["context"] = [""]

  return chunks


# 指定文件路径
input_file_path = (
  r"D:\codesforpython\rag\data\news_for_software.json"  # 输入的JSON文件路径
)
output_file_path = (
  r"D:\codesforpython\rag\data\news_for_software.json"  # 输出的JSON文件路径
)

# 加载数据
data = load_json(input_file_path)

# 处理数据
processed_data = process_data(data)

# 保存结果
save_json(processed_data, output_file_path)

print("数据处理完成，结果已保存。")
