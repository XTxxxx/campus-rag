import json
from typing import Union

from DrissionPage import Chromium

def get_intro():
    tab = Chromium().latest_tab
    links = get_links()
    res: list[dict[str, Union[str, list]]] = []
    for teacher in links:
        link = links[teacher]
        dic = {'cleaned_chunk': '', 'context': []}
        dic.update({'source': link})
        tab.get(link)
        div1 = tab.eles('tag:p')
        dic.update({'chunk': ', '.join([i.text for i in div1])})
        res.append(dic)
    with open("../../../data/nju_se_teacher.json", "w") as json_file:
        json.dump(res, json_file)
    print('Done')

def get_links() -> dict[str, str]:
    res = dict()
    tab = Chromium().latest_tab
    tab.get('https://software.nju.edu.cn/szll/szdw/index.html')
    tds = tab.eles('tag:td')
    for i in tds:
        try:
            tag = i.ele('tag:a')
            link = tag.link
            print(tag.text, link)
            res.update({tag.text: link})
        except Exception as e:
            print(e)
    return res

if __name__ == '__main__':
    get_intro()