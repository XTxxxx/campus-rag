import json
import spacy

# 加载中文语言模型
nlp = spacy.load("zh_core_web_sm")

# 定义源链接
source = "https://jw.nju.edu.cn/24748/list.htm"


# 从TXT文件读取文本
def read_txt_file(file_path):
    """读取TXT文件并返回文本内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# 语义分块函数
def semantic_chunking(text):
    """
    使用spaCy对文本进行语义分块。
    """
    doc = nlp(text)
    chunks = []
    current_chunk = []

    for sent in doc.sents:
        current_chunk.append(sent.text)
        if len(current_chunk) >= 2:  # 每两个句子为一个语义块
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    # 添加剩余的句子
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# 处理TXT文件并生成JSON输出
def process_txt_to_json(file_path):
    """从TXT文件读取文本，进行语义分块，并生成JSON格式输出"""
    # 读取TXT文件
    text = read_txt_file(file_path)
    #print(text)

    # 语义分块
    json_chunks = []
    chunks = semantic_chunking(text)

    # 生成JSON对象
    for chunk in chunks:
        json_obj = {
            "source": source,
            "chunk": chunk,
            "cleaned_chunk": "",  # 根据需要清理文本，可以在此填入清理后的结果
            "context": []  # 根据需要填充上下文信息
        }
        json_chunks.append(json_obj)

    # 将结果转换为JSON格式
    json_output = json.dumps(json_chunks, ensure_ascii=False, indent=4)
    return json_output


# 示例TXT文件路径
txt_file_path = r""

# 处理TXT文件并输出结果
json_output = process_txt_to_json(txt_file_path)

with open("../../../data/student_manual.json", "w", encoding='utf-8') as f:
     f.write(json_output)
