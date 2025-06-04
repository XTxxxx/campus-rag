import json


def get_keyword_explain(path: str) -> str:
  """
  Get the keyword explain for the given path.
  Args:
      path (str): The path to the file or directory.
  Returns:
      str: The keyword explain.
  """
  with open(path) as f:
    data = json.load(f)
  explain_str = ""
  for item in data:
    if "keyword" in item and "explanation" in item:
      explain_str += f"{item['keyword']}: {item['explanation']}\n"
  return explain_str.strip() if explain_str else "No keyword explanations found."
