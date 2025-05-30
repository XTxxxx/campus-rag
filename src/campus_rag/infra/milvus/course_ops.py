"""
support operations for milvus, e.g. select by keywords
search in meta field
"""

from typing import Optional
from pymilvus import MilvusClient, DataType, WeightedRanker, AnnSearchRequest
from campus_rag.constants.milvus import (
  MILVUS_URI,
  COLLECTION_NAME,
  COURSES_COLLECTION_NAME,
  START_FIELD,
)

# from campus_rag.infra.milvus.init import campus_rag_mc as client
from campus_rag.infra.embedding import embedding_model, sparse_embedding_model
import logging

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
client = MilvusClient(uri=MILVUS_URI)


def _select(
  collection_name: str, _type: str, kwargs: dict, output_fields: list[str], limit=-1
) -> list[dict]:
  """Transform the input parameters into a query for the Milvus database.
      We search from meta field

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
    condition = START_FIELD  # start from meta field
    for i, key in enumerate(keys):
      _value = f'"{kwargs[key]}"' if type(kwargs[key]) is str else kwargs[key]
      _key = f'"{key}"' if type(key) is str else key
      condition += f"[{_key}] {_types[_type]} {_value}"
      if i != len(keys) - 1:
        condition += f" AND {START_FIELD}"
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
    collection_name=COURSES_COLLECTION_NAME,
    filter="",
    output_fields=["*"],
    limit=limit,
  )


def _construct_filter_expr(
  _type: str,
  parent_key: str = None,
  inner_keys: list[list[list[str]]] = None,
  values: list = None,
  **kwargs,
) -> str:
  conditions = ""
  for i, keys in enumerate(inner_keys):
    condition = START_FIELD
    if parent_key and keys and values:
      if len(keys) != len(values):
        raise ValueError("inner_keys and values must have the same length")
      _parent_key = f'"{parent_key}"' if type(parent_key) == str else parent_key
      for i, (inner_key, value) in enumerate(zip(keys, values)):
        condition += f"[{_parent_key}]"
        for key in inner_key:
          _key = f'"{key}"' if type(key) == str else key
          condition += f"[{_key}]"
        _value = f'"{value}"' if type(value) == str else value
        condition += f" {_types[_type]} {_value}"
        if i != len(keys) - 1:
          condition += f" AND {START_FIELD}"  # add && restriction
    conditions = (
      f"({condition})" if conditions == "" else f"{conditions} OR ({condition})"
    )
  # considering other possibly existing restriction
  for key, value in kwargs.items():
    _value = f'"{value}"' if type(value) == str else value
    _key = f'"{key}"' if type(key) == str else key
    if conditions == "":  # avoid special condition, e.g. inner_keys=[](empty list)
      conditions = f"{START_FIELD}[{_key}] {_types[_type]} {_value}"
    else:
      conditions += f" AND {START_FIELD}[{_key}] {_types[_type]} {_value}"
  return conditions


def select_from_inner_datas(
  collection_name: str,
  output_fields: list[str],
  _type: str,
  parent_key: str,
  inner_keys: list[list[list[str]]],
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
      inner_keys (list[list[list[str]]]): inner filter's keys, first dim means different inner keys, second dim is used to merge a total key
        first dim make OR expr; second & third dim make complete filter
      values (list): inner filter's values, relative to inner-keys
      limit (int): max_length of result, -1 represents no limit

  Returns:
      A list of dicts, each dict represents a result
  """
  try:
    condition = _construct_filter_expr(_type, parent_key, inner_keys, values, **kwargs)
    result = client.query(
      collection_name=collection_name, filter=condition, output_fields=output_fields
    )
    return result[:limit]
  except Exception as e:
    logger.error(f"Error in select_from_inner_datas: {e}")


async def filter_with_embedding_select(
  mc: MilvusClient,
  collection_name: str,
  output_fields: list[str],
  _type: str,
  query: str,
  search_params: dict,
  parent_key: str = None,
  inner_keys: list[list[str]] = None,
  values: list = None,
  limit=2,
  **kwargs,
) -> list[dict]:
  # embedding for query
  query_embedding = embedding_model.encode(query, normalize_embeddings=True)
  query_sparse_embedding = sparse_embedding_model([query])["sparse"][[0]]
  sparse_weight = 0.67
  dense_weight = 1 - sparse_weight
  reranker = WeightedRanker(sparse_weight, dense_weight)
  condition = _construct_filter_expr(_type, parent_key, inner_keys, values, **kwargs)
  req = AnnSearchRequest(
    [query_embedding],
    "embedding",
    search_params,
    limit=limit,
    expr=condition,
  )
  sparse_req = AnnSearchRequest(
    [query_sparse_embedding],
    "sparse_embedding",
    search_params,
    limit=limit,
    expr=condition,
  )
  results = mc.hybrid_search(
    collection_name,
    [req, sparse_req],
    limit=limit,
    ranker=reranker,
    output_fields=output_fields,
    offset=0,
  )[0]
  return results


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
      inner_keys=[
        [[0, "time", "weeks"], [0, "time", "day_in_week"], [0, "place"]],
        [[1, "time", "weeks"], [1, "time", "day_in_week"], [1, "place"]],
      ],
      values=["1-16周", 4, "逸B-201"],
      limit=2,
      department_name="法学院",
      # grades=2022,  # trigger error
    )
  )
  # print(select_eq(COURSES_COLLECTION_NAME, output_fields=["*"], limit=2, course_number="06020300"))
  # print(select_all(limit=16000))
  # print(client.list_collections())
