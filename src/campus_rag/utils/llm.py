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
redis_client = redis.Redis(host="localhost", port=6379, password="123456", decode_responses=True)

logging.basicConfig(level=logging.DEBUG)
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
    return cached_response

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
  cache_key = get_cache_key(prompts)
  cached_response = redis_client.get(cache_key)

  if cached_response:
    logging.info("LLM cache hit (async)")
    return cached_response
    
  retries = 3
  tries = 0
  while tries < retries:
    try:
      res = (
        (
          await _llm_bare_async.chat.completions.create(
            model=_llm_name,
            messages=prompts,
          )
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


def llm_chat_stream(prompts: Prompts) -> Generator:
  cache_key = get_cache_key(prompts)
  cached_response = redis_client.get(cache_key)

  if cached_response:
    logging.info("LLM cache hit (stream)")
    # For streaming, yield the cached response as a single chunk
    class FakeStreamItem:
      def __init__(self, content):
        self.choices = [type('obj', (object,), {
          'delta': type('obj', (object,), {'content': content})
        })]
    
    yield FakeStreamItem(cached_response)
    return

  retries = 3
  tries = 0
  while tries < retries:
    try:
      # Create a collector for the full response
      full_response = []
      
      # Get the stream
      stream = _llm_bare.chat.completions.create(
        model=_llm_name,
        messages=prompts,
        stream=True,
      )
      
      # Process the stream while collecting the full response
      for chunk in stream:
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
          full_response.append(chunk.choices[0].delta.content)
        yield chunk
      
      # Cache the complete response
      complete_response = "".join(full_response).strip()
      redis_client.set(cache_key, complete_response, ex=60 * 60 * 24)  # cache for 1 day
      return
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )


def structure_llm_chat(prompts, model: BaseModel):
  cache_key = get_cache_key(prompts)
  cached_response = redis_client.get(cache_key)

  if cached_response:
    logging.info("LLM cache hit (structured)")
    # Deserialize the cached structured response
    try:
      return model(**json.loads(cached_response))
    except Exception as e:
      logging.error(f"Failed to deserialize cached structured response: {e}")
      # Continue with the API call if deserialization fails
  
  llm_strcture = _llm_langchain.with_structured_output(model)
  retries = 3
  tries = 0
  while tries < retries:
    try:
      result = llm_strcture.invoke(prompts)
      # Cache the structured result
      try:
        serialized_result = json.dumps(result.dict())
        redis_client.set(cache_key, serialized_result, ex=60 * 60 * 24)  # cache for 1 day
      except Exception as e:
        logging.error(f"Failed to cache structured response: {e}")
      return result
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      retries -= 1
      if retries == 0:
        raise RuntimeError(
          f"Failed to get response from Qwen API after {retries} retries"
        )
