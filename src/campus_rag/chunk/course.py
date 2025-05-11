import pandas as pd
import json

# 读取 Excel 文件
excel_file = r"C:\Users\18736\Desktop\course.xlsx"
df = pd.read_excel(excel_file)

# 填充空值
df = df.fillna("")

# 定义存储合并后的 JSON 对象的字典
merged_data = {}
source = "https://ehallapp.nju.edu.cn/jwapp/sys/kcbcx/*default/index.do?t_s=1742805619291&amp_sec_version_=1&gid_=R3RzYTJvSmg2NDhTdUJSL1U0NURrT3lickJoYm43Z1EwWkN2TmJLRmFCWGx1dWUyNmxhbzZ6TDBUWE1VRzhsMyt3ZktSVG93MHFvSFJrYXdvYVBEOFE9PQ&EMAP_LANG=zh&THEME=#/qxkcb"

# 遍历每一行
for _, row in df.iterrows():
  # 提取关键词
  keyword1 = row.iloc[2].strip()  # 去除两端空格
  keyword3 = row.iloc[6].strip()  # 去除两端空格

  # 构建关键词元组
  keywords = keyword1 + " " + keyword3

  chunk = " ".join(str(value) for value in row[0:] if value)  # 去掉空值

  # 构建 JSON 对象
  json_obj = {
    "source": source,
    "chunk": chunk.strip(),  # 去除两端空格
    "cleaned_chunk": keywords,  # 可以在后面增加清洗逻辑
    "context": [],
  }

  merged_data[keywords] = json_obj

# 将合并后的 JSON 数据转为列表
final_json_data = list(merged_data.values())

# 将 JSON 数据写入文件
output_file_path = r"D:\codesforpython\rag\data\course.json"
with open(output_file_path, "w", encoding="utf-8") as f:
  json.dump(final_json_data, f, ensure_ascii=False, indent=2)

print("课表已经生成")
