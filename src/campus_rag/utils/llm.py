"""
Wrapper for OpenAI API
"""

import hashlib
import json
import os
import logging
import redis
from openai import OpenAI, AsyncOpenAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import TypedDict, Generator

_ALI_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
redis_client = redis.Redis(host="localhost", port=6379, db=0)

logging.basicConfig(level=logging.INFO)
_llm_name = "qwen-max-2025-01-25"
_llm_key = os.getenv("QWEN_API_KEY")
_llm_bare = OpenAI(base_url=_ALI_URL, api_key=_llm_key)

_llm_bare_async = AsyncOpenAI(base_url=_ALI_URL, api_key=_llm_key)

_llm_langchain = ChatOpenAI(
  model=_llm_name,
  base_url=_ALI_URL,
  api_key=_llm_key,
)


class Message(TypedDict):
  role: str
  content: str


Prompts = list[Message]


def get_cache_key(prompt: Prompts) -> str:
  serialized_prompt = json.dumps(prompt, ensure_ascii=False, sort_keys=True)
  return f"llm_cache:{hashlib.sha256(serialized_prompt.encode()).hexdigest()}"


def llm_chat(prompts: Prompts) -> str:
  cache_key = get_cache_key(prompts)
  cached_response = redis_client.get(cache_key)

  if cached_response:
    logging.info("LLM cache hit")
    return cached_response.decode("utf-8")

  retries = 3
  tries = 0
  while tries < retries:
    try:
      res = (
        _llm_bare.chat.completions.create(
          model=_llm_name,
          messages=prompts,
        )
        .choices[0]
        .message.content.strip()
      )
      redis_client.set(cache_key, res, ex=60 * 60 * 24)  # cache for 1 day
      return res
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )


async def llm_chat_async(prompts: Prompts) -> str:
  retries = 3
  tries = 0
  while tries < retries:
    try:
      return (
        (
          await _llm_bare_async.chat.completions.create(
            model=_llm_name,
            messages=prompts,
          )
        )
        .choices[0]
        .message.content.strip()
      )
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )


def llm_chat_stream(prompts: Prompts) -> Generator:
  retries = 3
  tries = 0
  while tries < retries:
    try:
      return _llm_bare.chat.completions.create(
        model=_llm_name,
        messages=prompts,
        stream=True,
      )
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )


def structure_llm_chat(prompts, model: BaseModel):
  llm_strcture = _llm_langchain.with_structured_output(model)
  retries = 3
  tries = 0
  while tries < retries:
    try:
      return llm_strcture.invoke(prompts)
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )
