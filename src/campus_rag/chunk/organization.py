import pandas as pd
import json

# 读取 Excel 表格（可以更改为其他格式，如 CSV）
df = pd.read_excel(r"C:\Users\18736\Desktop\社团活动.xlsx")
print(df)

# 初始化一个空列表来保存每一行的 JSON
json_list = []

# 遍历每一行，将其转换为字典
for index, row in df.iterrows():
    if len(row) > 0:  # 确保行不为空
        title = row.iloc[0]  # 使用 iloc 访问第一个元素
        # Convert each item to a string before joining
        data = " ".join(str(item) for item in row.iloc[1:])  # 其余的列转为字符串并连接
        json_object = {'cleaned_chunk': title, 'chunk': data,'source':"",'context':[]}
        json_list.append(json_object)

# 将列表转换为 JSON 字符串
json_str = json.dumps(json_list, ensure_ascii=False, indent=4)

# 将 JSON 字符串写入文件
with open(r'D:\codesforpython\rag\data\organization.json', 'w', encoding='utf-8') as f:
    f.write(json_str)