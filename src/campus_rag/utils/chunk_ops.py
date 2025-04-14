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


def construct_embedding_key(chunk: Chunk) -> str:
  """
  Construct a unique key for the chunk based on its content.
  """
  if "cleaned_chunk" in chunk and chunk["cleaned_chunk"]:
    cur_chunk = chunk["cleaned_chunk"]
  else:
    cur_chunk = chunk["chunk"]
  context = chunk["context"]
  if isinstance(context, str):
    context_str = context
  else:
    context_str = " ".join(context)
  return chunk["source"] + context_str + f" {cur_chunk}"
