from src.campus_rag.utils.llm import llm_chat_stream
from typing import AsyncGenerator
from src.campus_rag.conversation import ChatMessage

_HistoryLength = 4096

SYSTEM_PROMPT = {
  "role": "system",
  "content": """
    你是 Whaledge Copilot，南京大学智能校园信息助手。由南京大学软件学院 9loong Team 开发，专注于回答与南京大学校园相关的问题。提供学术、生活和校园活动等方面的信息和帮助。
    你的回答应该生动活泼，但简洁明确。你可以使用 Markdown 格式来增强回答的可读性，也可以适度加一些emoji表情来增加趣味性。
    请用中文回答问题。
  """,
}


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


def generate_answer(
  query: str, chunks: list[str], history: list[ChatMessage]
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

  return llm_chat_stream(
    [SYSTEM_PROMPT] + get_history_prompt(history) + [prompt_content]
  )
