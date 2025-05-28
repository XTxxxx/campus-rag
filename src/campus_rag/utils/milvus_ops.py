"""
support operations for milvus, e.g. select by keywords
"""

from pymilvus import MilvusClient, DataType, connections, Collection, AnnSearchRequest, WeightedRanker
from src.campus_rag.utils.const import *

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


def _select(
  collection_name: str, _type: str, kwargs: dict, output_fields: list[str], limit=-1
) -> list[dict]:
  try:
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
      collection_name=collection_name, filter=condition, output_fields=output_fields
    )
    return result[:limit]
  except Exception as e:
    raise e
  finally:
    return [{"msg": "Something error happened"}]


def select_eq(
  collection_name: str, output_fields: list[str], limit=-1, **kwargs
) -> list[dict]:
  """
  equal search
  see doc in select_like
  """
  return _select(collection_name, "eq", kwargs, output_fields, limit)


def select_diy(
  collection_name: str, condition: str, output_fields: list[str], limit=-1
) -> list[dict]:
  """
  best recommended select function, with the least limitation to design specific clause
  """
  result = client.query(
    collection_name=collection_name, filter=condition, output_fields=output_fields
  )
  return result[:limit]


def select_like(
  collection_name: str, output_fields: list[str], limit=-1, **kwargs
) -> list[dict]:
  """
  fuzzy search
  given an example for kwargs:
  e.g. if I want to search for info that with title containing "Nanjing", then passed by
  select_like(cname, fields, title="%Nanjing%")
  :param collection_name
  :param output_fields
  :param kwargs: the search condition
  :param limit max_length of result
  """
  return _select(collection_name, "like", kwargs, output_fields, limit)


def select_all(limit: int) -> list[dict]:
  return client.query(
    collection_name=COLLECTION_NAME,
    filter="",
    output_fields=["*"],
    limit=limit,
  )


def _construct_filter_expr(_type: str, parent_key: str=None, inner_keys: list[list[str]]=None, values: list=None, **kwargs):
  condition = ""
  if parent_key and inner_keys and inner_keys:
    if len(inner_keys) != len(values):
      raise ValueError("inner_keys and values must have the same length")
    for i, (inner_key, value) in enumerate(zip(inner_keys, values)):
      condition += f"{parent_key}"
      for key in inner_key:
        key = f'"{key}"' if type(key) == str else key
        condition += f"[{key}]"
      value = f'"{value}"' if type(value) == str else value
      condition += f" {_types[_type]} {value}"
      if i != len(inner_keys) - 1:
        condition += f" AND "  # add && restriction
  # considering other possibly existing restriction
  for key, value in kwargs.items():
    value = f'"{value}"' if type(value) == str else value
    if condition == "":  # avoid special condition, e.g. inner_keys=[](empty list)
      condition = f"{key} {_types[_type]} {value}"
    else:
      condition += f" AND {key} {_types[_type]} {value}"
  return condition


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
  """
  also recommended select function, almost feat all operations by select, but flexibility is worse than DIY
  select value from the key-value pair in collections: \n
  e.g. 'time_place': [{'time': ..., ...}, 'place': ...] \n
  this function will select info from 'time_place'->value (when or where)
  :param collection_name
  :param output_fields:
  :param _type: select type
  :param parent_key: selected values' parent key in collections
  :param inner_keys: inner filter's keys, first dim means different inner keys, second dim is used to merge a total key
  :param values: inner filter's values, relative to inner-keys
  :param limit: max_length of result, -1 represents no limit
  :param kwargs other restriction
  for inner_kwargs, given an example: \n
  inner_keys=[["time", "weeks"]], value=["1-16周"]
  """
  try:
    condition = _construct_filter_expr(_type, parent_key, inner_keys, values, **kwargs)
    result = client.query(
      collection_name=collection_name, filter=condition, output_fields=output_fields
    )
    return result[:limit]
  except Exception as e:
    raise e
  finally:
    return [{"msg": "Something error happened"}]


def filter_with_embedding_select(
        mc: MilvusClient, collection_name: str,
        output_fields: list[str],
        _type: str,
        query: str, search_params: dict,
        parent_key: str=None,
        inner_keys: list[list[str]]=None,
        values: list=None,
        limit=2,
        **kwargs,
):
  # embedding for query
  query_embedding = embedding_model.encode(query, normalize_embeddings=True)
  # query_sparse_embedding = sparse_embedding_model([query])["sparse"][[0]]
  reranker = WeightedRanker(1)
  condition = _construct_filter_expr(_type, parent_key, inner_keys, values, **kwargs)
  req = AnnSearchRequest(
    [query_embedding],
    "embedding",
    search_params,
    limit=10,
    expr=condition,
  )
  results = mc.hybrid_search(
    collection_name,
    [req],
    limit=limit,
    ranker=reranker,
    output_fields=output_fields,
  )
  return results


def drop_collections(mc: MilvusClient, collection_name: str):
  """
  Drop the collection if it exists.
  """
  if mc.has_collection(collection_name):
    mc.drop_collection(collection_name)
    print(f"Successfully dropped collection {collection_name}")
  else:
    print(f"Collection {collection_name} does not exist")


def create_course_collection(mc: MilvusClient, collection_name: str, embedding_model):
  # for testing select function's correctness
  if mc.has_collection(collection_name):
    raise ValueError(f"Collection {collection_name} already exists")
  schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=True)
  # create a schema for course list
  schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
  schema.add_field(
    field_name="embedding",
    datatype=DataType.FLOAT_VECTOR,
    dim=embedding_model.get_sentence_embedding_dimension(),
  )
  schema.add_field(field_name="sparse_embedding", datatype=DataType.SPARSE_FLOAT_VECTOR)
  schema.add_field("course_name", DataType.VARCHAR, max_length=1024)
  schema.add_field("course_number", DataType.VARCHAR, max_length=1024)
  schema.add_field("teacher_name", DataType.VARCHAR, max_length=1024)
  schema.add_field("department_name", DataType.VARCHAR, max_length=1024)
  schema.add_field("campus", DataType.VARCHAR, max_length=1024)
  schema.add_field("reference_book", DataType.VARCHAR, max_length=2**15)
  schema.add_field("teaching_class_id", DataType.VARCHAR, max_length=1024)
  schema.add_field("hours", DataType.INT16)
  schema.add_field("school_term", DataType.VARCHAR, max_length=1024)
  # time_place_field = FieldSchema(
  #   name="time_place",
  #   dtype=DataType.JSON,
  # )
  schema.add_field("time_place", DataType.JSON)
  schema.add_field("teaching_purpose", DataType.VARCHAR, max_length=65535)
  schema.add_field("summary", DataType.VARCHAR, max_length=65535)
  schema.add_field(
    "grades",
    DataType.ARRAY,
    element_type=DataType.INT16,
    max_capacity=10,  # array field using element_type
  )
  # add indexes
  index_params = mc.prepare_index_params()
  # vector field must have an index
  index_params.add_index(
    "embedding",
    index_type="FLAT",
    metric_type="IP",
  )
  index_params.add_index(
    "sparse_embedding", index_type="SPARSE_INVERTED_INDEX", metric_type="IP"
  )
  index_params.add_index("course_number")
  index_params.add_index("teacher_name")
  index_params.add_index("course_name")
  # start creating
  mc.create_collection(
    collection_name=collection_name, schema=schema, index_params=index_params
  )
  print(f"Created collection {collection_name}")


# test
if __name__ == "__main__":
  mc = MilvusClient(uri=MILVUS_URI)
  # create_course_collection(mc, COURSES_COLLECTION_NAME)
  # drop_collections(MilvusClient(uri=MILVUS_URI), COURSES_COLLECTION_NAME)
  # print(select_like(COURSES_COLLECTION_NAME, output_fields=["*"], course_number="06020300"))
  search_params = {
    "metric_type": "IP",
    "params": {},
  }
  query = """
    事少分高
  """
  res = filter_with_embedding_select(
    mc, COURSES_COLLECTION_NAME, output_fields=["*"], _type="eq",
    query=query, search_params=search_params,
    parent_key="time_place",
    inner_keys=[["time", "weeks"], ["time", "day_in_week"], ["place"]],
    values=["1-16周", 4, "逸B-201"],
    limit=2,
    department_name="法学院",
    grades=[2022],
  )
  print(res[:2])
  # print(
  #   select_from_inner_datas(
  #     COURSES_COLLECTION_NAME,
  #     ["*"],
  #     "eq",
  #     "time_place",
  #     inner_keys=[["time", "weeks"], ["time", "day_in_week"], ["place"]],
  #     values=["1-16周", 4, "逸B-201"],
  #     limit=2,
  #     # department_name="法学院",
  #     grades=2022  # trigger error
  #   )
  # )
  # print(select_eq(output_fields=["*"], course_number="06020300"))
  # print(select_all(limit=16000))
