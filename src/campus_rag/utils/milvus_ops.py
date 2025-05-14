"""
support operations for milvus, e.g. select by keywords
"""

from pymilvus import MilvusClient
from const import *

client = MilvusClient(uri=MILVUS_URI)

_types = {
  "eq": "==",
  "neq": "!=",
  "ge": ">=",
  "gt": ">",
  "le": "<=",
  "lt": "<",
  "like": "like",
}


def _select(_type: str, kwargs: dict) -> list:
  keys = kwargs.keys()
  condition = ""
  for i, key in enumerate(keys):
    if type(kwargs[key]) == str:
      kwargs[key] = f'"{kwargs[key]}"'
    condition += f"{key} {_types[_type]} {kwargs[key]}"
    if i != len(keys) - 1:
      condition += f" AND "
  # print(condition)
  result = client.query(
    collection_name=COLLECTION_NAME, filter=condition, output_fields=["*"]
  )
  return result


def select_eq(**kwargs) -> list:
  return _select("eq", kwargs)


def select_diy(condition: str) -> list:
  result = client.query(
    collection_name=COLLECTION_NAME, filter=condition, output_fields=["*"]
  )
  return result


def select_like(**kwargs) -> list:
  return _select("like", kwargs)


if __name__ == "__main__":
  print(select_like(chunk="%Nanjing%"))
