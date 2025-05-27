"""
support operations for milvus, e.g. select by keywords
"""

from typing import Optional
from pymilvus import MilvusClient, DataType
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
  COURSES_COLLECTION_NAME,
)
import logging

client = MilvusClient(uri=MILVUS_URI)
logger = logging.getLogger(__name__)

_types = {
  "eq": "==",
  "neq": "!=",
  "ge": ">=",
  "gt": ">",
  "le": "<=",
  "lt": "<",
  "like": "like",
}


def _select(
  collection_name: str, _type: str, kwargs: dict, output_fields: list[str], limit=-1
) -> list[dict]:
  """Transform the input parameters into a query for the Milvus database.

  Args:
      collection_name (str): The name of the collection to query.
      _type (str): The type of query (e.g., "eq", "like").
      kwargs (dict): The query parameters.
      output_fields (list[str]): The fields to include in the output.
      limit (int, optional): The maximum number of results to return. Defaults to -1 (no limit).

  Returns:
      list[dict]: The query results.
  """
  try:
    keys = kwargs.keys()
    condition = ""
    for i, key in enumerate(keys):
      if type(kwargs[key]) is str:
        kwargs[key] = f'"{kwargs[key]}"'
      condition += f"{key} {_types[_type]} {kwargs[key]}"
      if i != len(keys) - 1:
        condition += " AND "
    logger.debug(condition)
    result = client.query(
      collection_name=collection_name, filter=condition, output_fields=output_fields
    )
    return result[:limit]
  except Exception as e:
    logger.error(f"Error in _select: {e}")
    return [{"msg": "Something error happened"}]


def select_eq(
  collection_name: str, output_fields: list[str], limit=-1, **kwargs
) -> list[dict]:
  """equal search, see doc in select_like"""
  return _select(collection_name, "eq", kwargs, output_fields, limit)


def select_diy(
  collection_name: str, condition: Optional[str], output_fields: list[str], limit=-1
) -> list[dict]:
  """best recommended select function, with the least limitation to design specific claus"""
  result = client.query(
    collection_name=collection_name,
    filter=condition,
    output_fields=output_fields,
    limit=limit,
  )
  return result


def select_like(
  collection_name: str, output_fields: list[str], limit=-1, **kwargs
) -> list[dict]:
  """Fuzzy search

  Args:
      collection_name (str): name of the collection
      output_fields (list[str]): fields to be returned
      limit (int): max_length of result


  Kwargs:
      given an example for kwargs, if I want to search for info that with title containing "Nanjing", then passed by:
      title = "%Nanjing%" \n
  """
  return _select(collection_name, "like", kwargs, output_fields, limit)


def select_all(limit: int) -> list[dict]:
  return client.query(
    collection_name=COLLECTION_NAME,
    filter="",
    output_fields=["*"],
    limit=limit,
  )


def select_from_inner_datas(
  collection_name: str,
  output_fields: list[str],
  _type: str,
  parent_key: str,
  inner_keys: list[list[str]],
  values: list,
  limit=-1,
  **kwargs,
) -> list[dict]:
  """Also recommended select function, almost feat all operations by select, but flexibility is worse than DIY. \n
  Select value from the key-value pair in collections: e.g. 'time_place': [{'time': ..., ...}, 'place': ...] \n
  this function will select info from 'time_place'->value (when or where)

  Args:
      collection_name (str): name of the collection
      output_fields (list[str]): fields to be returned
      _type (str): select type
      parent_key (str): selected values' parent key in collections
      inner_keys (list[list[str]]): inner filter's keys, first dim means different inner keys, second dim is used to merge a total key
      values (list): inner filter's values, relative to inner-keys
      limit (int): max_length of result, -1 represents no limit

  Returns:
      A list of dicts, each dict represents a result
  """
  try:
    if len(inner_keys) != len(values):
      raise ValueError("inner_keys and values must have the same length")
    condition = ""
    for i, (inner_key, value) in enumerate(zip(inner_keys, values)):
      condition += f"{parent_key}"
      for key in inner_key:
        key = f'"{key}"' if type(key) is str else key
        condition += f"[{key}]"
      value = f'"{value}"' if type(value) is str else value
      condition += f" {_types[_type]} {value}"
      if i != len(inner_keys) - 1:
        condition += " AND "  # add && restriction
    # considering other possibly existing restriction
    for key, value in kwargs.items():
      value = f'"{value}"' if type(value) is str else value
      if condition == "":  # avoid special condition, e.g. inner_keys=[](empty list)
        condition = f"{key} {_types[_type]} {value}"
      else:
        condition += f" AND {key} {_types[_type]} {value}"
    result = client.query(
      collection_name=collection_name,
      filter=condition,
      output_fields=output_fields,
      limit=limit,
    )
    return result
  except Exception as e:
    logger.error(f"Error in select_from_inner_datas: {e}")


# test
if __name__ == "__main__":
  mc = MilvusClient(uri=MILVUS_URI)
  # create_course_collection(mc, COURSES_COLLECTION_NAME)
  # drop_collections(MilvusClient(uri=MILVUS_URI), COURSES_COLLECTION_NAME)
  # print(select_like(COURSES_COLLECTION_NAME, output_fields=["*"], course_number="06020300"))
  print(
    select_from_inner_datas(
      COURSES_COLLECTION_NAME,
      ["*"],
      "eq",
      "time_place",
      inner_keys=[["time", "weeks"], ["time", "day_in_week"], ["place"]],
      values=["1-16周", 4, "逸B-201"],
      limit=2,
      # department_name="法学院",
      grades=2022,  # trigger error
    )
  )
  # print(select_eq(output_fields=["*"], course_number="06020300"))
  # print(select_all(limit=16000))
