import json

if __name__ == "__main__":
    # 定义文件路径
    general_tag_file = "./data/course_general_tag.json"
    course_list_file = "./data/course_list.json"
    output_file = "./data/course_list_with_tags.json"

    # 读取 course_general_tag.json
    with open(general_tag_file, "r", encoding="utf-8") as f:
        general_tags = json.load(f)

    # 读取 course_list.json
    with open(course_list_file, "r", encoding="utf-8") as f:
        course_list = json.load(f)

    # 为每门课程添加 course_type
    for course in course_list:
        course_number = course.get("course_number", "")
        if course.get("department_name") == "体育部":
            course["course_type"] = "公共体育课"
        elif course_number.startswith("000"):
            course["course_type"] = "通修课"
        elif course_number in general_tags:
            course["course_type"] = general_tags[course_number]
        else:
            course["course_type"] = "专业课"

    # 保存结果到新的文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(course_list, f, ensure_ascii=False, indent=4)