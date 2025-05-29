from campus_rag.constants.prompt import SYSTEM_PROMPT
from campus_rag.utils.llm import llm_chat_astream
from typing import AsyncGenerator
from campus_rag.domain.rag.po import ChatMessage

_HistoryLength = 4096




def get_history_prompt(history: list[ChatMessage]) -> list[dict]:
  history = history[::-1]
  history_prompt = []
  length = 0
  while True:
    if len(history) == 0:
      break
    length += len(history[0].content)
    if length > _HistoryLength:
      break
    history_prompt.append(
      {
        "role": history[0].role,
        "content": history[0].content,
      }
    )
    history = history[1:]
  return history_prompt[::-1]


async def generate_answer(
  query: str, chunks: list[str], history: list[ChatMessage]
) -> AsyncGenerator:
  """Generate an answer for the given query and chunks.
  Args:
    query: The query string.
    chunks: List of chunks to use for generating the answer.
  Return:
    The generated answer as a string.
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

  return llm_chat_astream(
    [SYSTEM_PROMPT] + get_history_prompt(history) + [prompt_content]
  )
