import json
from typing import Union

def dump_course():
    res: list[dict[str, Union[str, list]]] = []
    with open('course.CSV', 'r', encoding='gbk') as file:
        for line in file:
            # 处理每一行数据
            processed_line = line.strip()  # 去除每行两端的空白符
            dic = {'cleaned_chunk': '', 'context': []}
            dic.update({'source': 'https://ehallapp.nju.edu.cn/jwapp/sys/kcbcx/*default/index.do?t_s=1742805619291&amp_sec_version_=1&gid_=R3RzYTJvSmg2NDhTdUJSL1U0NURrT3lickJoYm43Z1EwWkN2TmJLRmFCWGx1dWUyNmxhbzZ6TDBUWE1VRzhsMyt3ZktSVG93MHFvSFJrYXdvYVBEOFE9PQ&EMAP_LANG=zh&THEME=#/qxkcb'})
            dic.update({'chunk': processed_line})
            res.append(dic)
    with open("../../../data/course.json", "w") as json_file:
        json.dump(res, json_file)
    print('Done')

if __name__ == '__main__':
    dump_course()