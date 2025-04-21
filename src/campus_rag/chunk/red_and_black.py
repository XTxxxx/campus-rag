import pandas as pd
import json
from keybert import KeyBERT

kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")

# 读取 Excel 文件
excel_file = r'D:\下载\红黑榜_2024冬.xlsx'
df = pd.read_excel(excel_file)

df = df.fillna('')

# 定义存储合并后的 JSON 对象的字典
merged_data = {}

index = 1
# 遍历每一行
for _, row in df.iterrows():
    # 提取关键词
    if (not row.iloc[3] == "") and not row.iloc[0] and not row.iloc[1] and not row.iloc[2]:
        continue  # 跳过该行
    title1 = row.iloc[0]
    title2 = row.iloc[2]  # 去除两端空格

    # 构建关键词元组
    titles = (title1, title2)

    # 从第四列开始，拼接不为空的列
    chunk = ' '.join(str(value) for value in row[3:] if value)  # 去掉空值

    if chunk == "":
        continue

    chunk = ' '.join(str(value) for value in row[1:] if value)
    # 使用 KeyBERT 提取关键词
    keywords = kw_model.extract_keywords(chunk, keyphrase_ngram_range=(1, 2),use_mmr=False,stop_words=None,diversity=0.7,top_n=3)
    index+=1
    print(index)
    keywords = [kw[0] for kw in keywords]  # 只提取关键词，忽略置信度

    # 构建 JSON 对象
    json_obj = {
        "chunk": chunk.strip(),  # 去除两端空格
        "keywords": keywords,     # 提取的关键词
        "titles": list(titles)    # 将 titles 转为列表
    }

    if titles in merged_data:
        merged_data[titles]['chunk'] += ' ' + json_obj['chunk']
        merged_data[titles]['keywords'].extend(json_obj['keywords'])
    else:
        merged_data[titles] = json_obj

# 去重关键词
for key in merged_data:
    merged_data[key]['keywords'] = list(set(merged_data[key]['keywords']))

# 将合并后的 JSON 数据转为列表
final_json_data = list(merged_data.values())

# 将 JSON 数据写入文件
output_file_path = r'D:\codesforpython\rag\data\red_and_black_table.json'
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(final_json_data, f, ensure_ascii=False, indent=2)

print("红黑榜已经生成")