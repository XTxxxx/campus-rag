import pandas as pd
import json

# 读取 Excel 文件
excel_file = r'D:\下载\红黑榜_2024冬.xlsx'
df = pd.read_excel(excel_file)

# 填充空值
df = df.fillna('')

# 定义存储合并后的 JSON 对象的字典
merged_data = {}
source = "https://table.nju.edu.cn/external-apps/7aded834-74a2-43cc-b515-fb8e01656ef2/?page_id=phII"

# 遍历每一行
for _, row in df.iterrows():
    # 提取关键词
    keyword1 = row.iloc[0].strip()  # 去除两端空格
    keyword3 = row.iloc[2].strip()  # 去除两端空格

    # 构建关键词元组
    keywords = keyword1 + " " + keyword3

    # 从第四列开始，拼接不为空的列
    chunk = ' '.join(str(value) for value in row[0:] if value)  # 去掉空值

    # 构建 JSON 对象
    json_obj = {
        "source": source,
        "chunk": chunk.strip(),  # 去除两端空格
        "cleaned_chunk": keywords,  # 可以在后面增加清洗逻辑
        "context": [],
    }

    # 合并相同关键词的 JSON 对象
    if keywords in merged_data:
        # 如果已经存在，合并 chunk 内容
        merged_data[keywords]['chunk'] += ' ' + json_obj['chunk']
    else:
        # 如果不存在则加入新结构
        merged_data[keywords] = json_obj

# 将合并后的 JSON 数据转为列表
final_json_data = list(merged_data.values())

# 将 JSON 数据写入文件
output_file_path = r'D:\codesforpython\rag\data\red_and_black_table.json'
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(final_json_data, f, ensure_ascii=False, indent=2)

print("红黑榜已经生成")