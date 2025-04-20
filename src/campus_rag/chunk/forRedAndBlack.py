import pandas as pd
import json

# 读取 Excel 文件
excel_file = ''
df = pd.read_excel(excel_file)

df = df.fillna('')

# 转换为 JSON 的列表
json_data = []
source = "https://table.nju.edu.cn/external-apps/7aded834-74a2-43cc-b515-fb8e01656ef2/?page_id=phII"

# 遍历每一行
for index, row in df.iterrows():
    # 获取前三列
    first_three = ' '.join(map(str, row[:3].values))

    # 检查第二列和第三列是否同时为空
    if not row[3]:
        continue  # 跳过该行

    # 从第四列开始，拼接不为空的列
    for value in row[3:]:  # 从第四列开始遍历
        if value:  # 如果该列不为空
            chunk = first_three + ' ' + str(value)  # 拼接前三列和当前列

            # 构建 JSON 对象
            json_obj = {
                "source": source,
                "chunk": chunk.strip(),  # 去除两端空格
                "cleaned_chunk": "",
                "context": []
            }
            json_data.append(json_obj)

# 将 JSON 数据写入文件
with open('red_and_black_table.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print("红黑榜已经生成")