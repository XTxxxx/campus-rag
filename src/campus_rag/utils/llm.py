"""
Wrapper for OpenAI API
"""

import hashlib
import json
import os
import logging
import re
from openai import OpenAI, AsyncOpenAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import TypedDict, AsyncGenerator
from campus_rag.domain.course.po import ScheduleError
from campus_rag.infra.redis import redis_client

_ALI_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


logger = logging.getLogger(__name__)
_llm_name = "qwen-max-2025-01-25"
_llm_key = os.getenv("LCX_QWEN_API_KEY")
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


async def llm_chat_astream(prompts: Prompts) -> AsyncGenerator:
  cache_key = get_cache_key(prompts)
  cached_response = redis_client.get(cache_key)

  if cached_response:
    logging.info("LLM cache hit (stream)")
    yield cached_response
    return

  retries = 3
  tries = 0
  while tries < retries:
    try:
      stream = await _llm_bare_async.chat.completions.create(
        model=_llm_name,
        messages=prompts,
        stream=True,
      )
      full_response = []
      # Process the stream while collecting the full response
      async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is not None:
          full_response.append(content)
        yield content
      full_response_str = "".join(full_response).strip()
      redis_client.set(cache_key, full_response_str, ex=60 * 60 * 24)  # cache for 1 day
      return
    except Exception as e:
      logging.error(f"Errors occurred: {e}")
      tries += 1
      if tries == retries:
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
        redis_client.set(
          cache_key, serialized_result, ex=60 * 60 * 24
        )  # cache for 1 day
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


def parse_as_json(llm_output: str) -> dict:
  """Parse the LLM output as JSON."""
  try:
    return json.loads(llm_output)
  except json.JSONDecodeError:
    # Search for ```json ```
    json_match = re.search(r"```json\s*(.*?)\s*```", llm_output, re.DOTALL)
    if json_match:
      llm_output = json_match.group(1).strip()
      try:
        return json.loads(llm_output)
      except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from LLM output: {e}\n{llm_output}")
        raise ScheduleError
