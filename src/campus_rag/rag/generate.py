from src.campus_rag.utils.llm import llm_chat, llm_chat_stream
from typing import AsyncGenerator


def generate_answer(
  query: str,
  chunks: list[str],
) -> AsyncGenerator:
  """
  Generate an answer for the given query and chunks.
  :param query: The query string.
  :param chunks: List of chunks to use for generating the answer.
  :return: The generated answer as a string.
  """
  prompt_content = {
    "role": "user",
    "content": f"""
    ## Instruction ##
    Generate an answer according to the following context.
    ## Context ##
    {chunks}
    ## Query ##
    {query}
    """,
  }

  return llm_chat_stream([prompt_content])
