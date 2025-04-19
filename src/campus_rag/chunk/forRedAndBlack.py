import pandas as pd
import json

# 读取 Excel 文件
excel_file = 'D:\下载\红黑榜_2024冬.xlsx'  # 请将 'your_file.xlsx' 替换为你的文件路径
df = pd.read_excel(excel_file)

df = df.fillna('')

# 转换为 JSON 的列表
json_data = []
source = "https://table.nju.edu.cn/external-apps/7aded834-74a2-43cc-b515-fb8e01656ef2/?page_id=phII"

# 遍历每一行
for index, row in df.iterrows():
    # 将每一行的内容拼接为一个字符串
    chunk = ' '.join(map(str, row.values))
    # 构建 JSON 对象
    json_obj = {
        "source": source,
        "chunk": chunk,
        "cleaned_chunk": "",
        "context": []
    }
    json_data.append(json_obj)

# 将 JSON 数据写入文件
with open('red_and_black_table.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print("红黑榜已经生成")