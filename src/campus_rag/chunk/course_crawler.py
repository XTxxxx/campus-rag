import requests
import urllib
import json
import typer
import time
from tqdm import tqdm

TOKEN = 'desensitized'
COOKIE = 'desensitized'
STUDENT_CODE = 'desensitized'
RAW_PATH = "./data/course_raw.json"
LIST_PATH = "./data/course_list.json"
LCDM = 'desensitized'
TOTAL_COUNT = 3000
PAGE_SIZE = 50
DUMP_PER = 50

app = typer.Typer()

xk_headers = {
  "Accept": "application/json, text/javascript, */*; q=0.01",
  "Accept-Encoding": "gzip, deflate, br, zstd",
  "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
  "Cache-Control": "no-cache",
  "Connection": "keep-alive",
  "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
  "Cookie": COOKIE,
  "Host": "xk.nju.edu.cn",
  "Origin": "https://xk.nju.edu.cn",
  "Pragma": "no-cache",
  "Referer": f"https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token={TOKEN}",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
  "X-Requested-With": "XMLHttpRequest",
  "language": "zh_cn",
  "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": '"Windows"',
  "token": TOKEN,
}


@app.command()
def dump_course_list():
  json_output = []
  for i in range((TOTAL_COUNT + PAGE_SIZE - 1) // PAGE_SIZE):
    query_setting = {
      "data": {
        "studentCode": STUDENT_CODE,
        "electiveBatchCode": LCDM,
        "teachingClassType": "QB",
        "queryContent": "",
      },
      "pageSize": f"{PAGE_SIZE}",
      "pageNumber": f"{i}",
      "order": "",
    }
    payload = "querySetting=" + urllib.parse.quote_plus(
      str(query_setting).replace("'", '"')
    )

    response = requests.post(
      "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/elective/queryCourse.do",
      data=payload,
      headers=xk_headers,
      timeout=5,
    )

    if response.status_code != 200:
      print(f"Error: response status code {response.status_code}")
      return

    try:
      json_response = response.json()
    except json.JSONDecodeError:
      print("Error: Failed to decode JSON response")
      return
    json_output.extend(json_response["dataList"])
    time.sleep(0.5)
  with open(RAW_PATH, "w", encoding="utf-8") as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)


def parse_time_place(course) -> list:
  if "teachingTimeList" not in course or course["teachingTimeList"] is None:
    print(f"Warning: {course['courseName']} has no teaching time list")
    return []
  split_chars = [";", "\n"]
  places = []
  hit = False
  for char in split_chars:
    if char in course["teachingPlace"]:
      hit = True
      time_places = course["teachingPlace"].split(char)
      for time_place in time_places:
        places.append(time_place.split(" ")[-1])
      break
  if not hit:
    places = [course["teachingPlace"].split(" ")[-1]]
  times = []
  for time_arrange in course["teachingTimeList"]:
    new_time = {}
    new_time["weeks"] = time_arrange["weekName"]
    new_time["day_in_week"] = time_arrange["dayOfWeek"]
    new_time["begin_at"] = time_arrange["beginSection"]
    new_time["week_binary"] = time_arrange["week"]
    new_time["end_at"] = time_arrange["endSection"]
    times.append(new_time)
  if len(times) != len(places):
    breakpoint()
    print(f"Warning: {course['courseName']} has different time and place lengths")
  return [{"time": times[i], "place": places[i]} for i in range(len(times))]


@app.command()
def parse_course_list():
  with open(RAW_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
  course_list = data
  print(f"Total courses: {len(course_list)}")
  parsed_courses = []
  for course in course_list:
    new_course = {}
    new_course["course_name"] = course["courseName"]
    new_course["course_number"] = course["courseNumber"]
    new_course["teacher_name"] = course["teacherName"]
    new_course["department_name"] = course["departmentName"]
    new_course["campus"] = course["campusName"]
    new_course["teaching_class_id"] = course["teachingClassID"]
    new_course["hours"] = course["hours"]
    new_course["school_term"] = course["schoolTerm"]
    # Process the course time
    new_course["time_place"] = parse_time_place(course)
    new_course["grade"] = course["recommendGrade"]
    parsed_courses.append(new_course)
  with open(LIST_PATH, "w", encoding="utf-8") as f:
    json.dump(parsed_courses, f, ensure_ascii=False, indent=2)


@app.command()
def crawle_details():
  with open(LIST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
  dump_cnt = 0
  for course in tqdm(data):
    if "course_summary" in course:
      continue
    payload = {
      "kch": course["course_number"],
      "jxbid": course["teaching_class_id"],
      "xklcdm": LCDM,
    }
    response = requests.post(
      "https://xk.nju.edu.cn/xsxkapp/sys/xsxkapp/publicinfo/querykcxx.do",
      data=payload,
      headers=xk_headers,
      timeout=5,
    )
    if response.status_code != 200:
      print(f"Error: response status code {response.status_code}")
      continue
    try:
      course_detail = response.json()["data"]
    except json.JSONDecodeError:
      print("Error: Failed to decode JSON response")
      return
    if course_detail is None:
      print(f"{course['course_name']} has no course detail")
      continue
    course["course_summary"] = course_detail.get("coursesummary", "")
    course["teaching_plan"] = course_detail.get("teachingPlan", "")
    course["teaching_purpose"] = course_detail.get("teachingPurpose", "")
    course["reference_book"] = course_detail.get("referenceBook", "")
    dump_cnt += 1
    if dump_cnt == DUMP_PER:
      dump_cnt = 0
      with open(LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    time.sleep(0.1)


if __name__ == "__main__":
  app()
