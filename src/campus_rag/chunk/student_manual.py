import re
import json
from keybert import KeyBERT  # 导入 KeyBERT

# 创建 KeyBERT 模型实例
kw_model = KeyBERT()

# 读取文本文件
with open(r"C:\Users\18736\Desktop\student_manual.txt", "r", encoding="utf-8") as file:
  content = file.read()

# 使用正则表达式删除页码（类似于"82"的数字）
content = re.sub(r"\d+\s*", "", content)  # 匹配纯数字和可能跟随的空格

# 使用正则表达式分块，以分隔符为前缀分割
chunks = re.split(r"([一二三四五六七八九十]+\s*[、\.])", content)

# 将分隔词与对应内容合并并创建字典对象
result = []
for i in range(1, len(chunks), 2):
  # 分隔符后面的内容
  content_part = chunks[i].strip() + chunks[i - 1].strip()

  # 提取关键词，去掉前面的编号
  title_match = re.search(
    r"([一二三四五六七八九十]+\s*[、\.])?(.*?)(第\w+条)", content_part
  )
  if title_match:
    title = title_match.group(2).strip()  # 提取内容
  else:
    title = ""

  keywords = kw_model.extract_keywords(
    content_part, stop_words="english", top_n=5, use_mmr=True
  )

  # 提取关键词列表，包含单词和词组
  keywords_list = [keyword for keyword, _ in keywords]

  # 过滤以确保包含多个词的关键词
  keywords_list = [
    kw for kw in keywords_list if len(kw.split()) <= 2
  ]  # 仅保留最多有两个词的关键词

  json_obj = {
    "source": "",
    "chunk": content_part,
    "cleaned_chunk": title,
    "context": keywords_list,  # 添加提取的关键词
  }
  result.append(json_obj)

# 将结果写入JSON文件
with open(
  r"D:\codesforpython\rag\data\student_manual.json", "w", encoding="utf-8"
) as file:
  json.dump(result, file, ensure_ascii=False, indent=4)
