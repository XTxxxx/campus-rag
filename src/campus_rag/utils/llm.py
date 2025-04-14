"""
Wrapper for OpenAI API
"""

import os
import logging
from openai import OpenAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import TypedDict

logging.basicConfig(level=logging.INFO)
_llm_name = "qwen-max-2025-01-25"
_llm_key = os.getenv("QWEN_API_KEY")
_llm_bare = OpenAI(
  base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  api_key=_llm_key
)
_llm_langchain = ChatOpenAI(
  model=_llm_name,
  base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  api_key=_llm_key
)

class Message(TypedDict):
  role: str
  content: str

Prompts = list[Message]


def llm_chat(prompts: Prompts) -> str:
  retries = 3
  tries = 0
  while tries < retries:
    try:
      return (
        _llm_bare.chat.completions.create(
          model=_llm_name,
          messages=prompts,
        )
        .choices[0]
        .message.content.strip()
      )
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(f"Failed to get response from Qwen API after {retries} retries")

def structure_llm_chat(prompts, model: BaseModel):
  llm_strcture = _llm_langchain.with_structured_output(model)
  retries = 3
  tries = 0
  while tries < retries:
    try:
      return llm_strcture.invoke(
        prompts
      )
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(f"Failed to get response from Qwen API after {retries} retries")
