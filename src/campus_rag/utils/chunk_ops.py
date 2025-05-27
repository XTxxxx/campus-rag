from typing import TypedDict


class Chunk(TypedDict):
  """
  A class to represent a chunk of text.
  """

  chunk: str
  cleaned_chunk: str
  source: str
  context: list[str]
  embedding: list[float]
  sparse_embedding: list[float]


def get_chunk(chunk: Chunk) -> str:
  if "cleaned_chunk" in chunk and chunk["cleaned_chunk"]:
    return chunk["cleaned_chunk"]
  return chunk["chunk"]


def construct_embedding_key(chunk: Chunk) -> str:
  """
  Construct a unique key for the chunk based on its content.
  """
  cur_chunk = get_chunk(chunk)
  context = chunk["context"]
  if isinstance(context, str):
    context_str = context
  else:
    context_str = " ".join(context)
  return chunk["source"] + context_str + f" {cur_chunk}"


def construct_embedding_key_for_course(chunk: Chunk) -> str:
  """
  Construct a unique key for the course chunk based on its content.
  """
  introduction = ""
  if "summary" in chunk and chunk["summary"] is not None:
    introduction = introduction + chunk["summary"][:256]
  if "teaching_purpose" in chunk and chunk["teaching_purpose"] is not None:
    introduction = introduction + chunk["teaching_purpose"][:256]
  referecnce_book = chunk.get("reference_book", "")
  if referecnce_book:
    introduction = introduction + f" 参考教材：{referecnce_book}"
  embedding_key = f"""{chunk["course_name"]} {chunk["course_number"]}
老师：{chunk["teacher_name"]}，开课单位：{chunk["department_name"]}
介绍：{introduction}"""
  return embedding_key


def construct_meta_for_course(chunk: Chunk) -> dict:
  """
  Construct a metadata dictionary for the course chunk.
  """
  return {
    "course_name": chunk["course_name"],
    "course_number": chunk["course_number"],
    "teacher_name": chunk["teacher_name"],
    "department_name": chunk["department_name"],
    "campus": chunk["campus"],
    "reference_book": chunk["reference_book"],
    "teaching_class_id": chunk["teaching_class_id"],
    "hours": chunk["hours"],
    "school_term": chunk["school_term"],
    "time_place": chunk["time_place"],
    "grades": chunk.get("grades", []),
  }
