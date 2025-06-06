import logging
import json
from enum import Enum
import time
from pydantic import BaseModel
from typing import List
from campus_rag.constants.prompt import SYSTEM_PROMPT
from campus_rag.utils.llm import llm_chat_async, Message
from campus_rag.utils.keyword_explain import get_keyword_explain

logger = logging.getLogger(__name__)


class ReflectionCategory(Enum):
  """
  这里的逻辑是：
    对于无关问题，仅提供基本的上下文信息并回答
    相关问题但不足以回答的，就不会回答
    相关问题且足以回答的，直接提供答案
  """

  IRRELEVANT = 1  # 无关问题
  ANSWERABLE = 2  # 正常回答


class ReflectionResult(BaseModel):
  """Model for structured output from LLM reflection."""

  category: ReflectionCategory
  explanation: str


async def reflect_query(query: str, context: List[str], system_prompt: Message) -> dict:
  """
  A non-async version that returns a dictionary instead of a structured model.
  Useful for direct script execution and testing.

  :param query: The user's question
  :param context: List of context passages relevant to the query
  :return: A dictionary with category and explanation
  """
  time.sleep(1)
  logger.info("Reflecting on query and context...")

  context_text = "\n".join(
    [f"Passage {i + 1}: {ctx[:512]}" for i, ctx in enumerate(context)]
  )

  prompt_content = {
    "role": "user",
    "content": f"""
        ## Instruction ##
        Analyze the user's question and the provided context passages. 
        Determine if:
        1 问题和南京大学校园信息无关，或者是不需要使用上下文信息就能回答的问题（如打招呼信息）(category 1)
        2.问题相关，并且可以通过上下文回答(category 2)
        
        ## User Question ##
        {query}
        
        ## Term explanation ##
        {get_keyword_explain("./data/keywords.json")}
        
        ## Context Passages ##
        {context_text}
        
        Return your analysis in JSON format with the following structure:
        {{
            "category": <category number (1, 2)>,
            "explanation": "<your explanation for the classification>"
        }}

        Only provide the JSON, no other text.
        """,
  }

  response = await llm_chat_async([system_prompt, prompt_content])

  try:
    result = json.loads(response)
    logger.info(
      f"Reflection result: Category {result['category']} - {result['explanation']}"
    )
    return result
  except json.JSONDecodeError:
    logger.info("Initial JSON parsing failed, trying to clean response")
    cleaned_response = response.strip()

    if cleaned_response.startswith("```json"):
      cleaned_response = cleaned_response.replace("```json", "", 1).strip()
    elif cleaned_response.startswith("```"):
      cleaned_response = cleaned_response.replace("```", "", 1).strip()

    if cleaned_response.endswith("```"):
      cleaned_response = cleaned_response.rsplit("```", 1)[0].strip()

    try:
      result = json.loads(cleaned_response)
      logger.info(
        f"Reflection result after cleaning: Category {result['category']} - {result['explanation']}"
      )
      return result
    except Exception as e:
      logger.error(f"Error parsing reflection result after cleaning: {e}")
      return {
        "category": 2,
        "explanation": "Failed to analyze the query and context properly.",
      }
  except Exception as e:
    logger.error(f"Error parsing reflection result: {e}")
    return {
      "category": 2,
      "explanation": "Failed to analyze the query and context properly.",
    }


if __name__ == "__main__":
  query = "南京大学的图书馆开放时间是什么时候？"
  context = [
    "南京大学仙林校区的图书馆周一至周五开放时间为8:00-22:00，周末为9:00-21:00。",
    "南京大学有多个校区，包括仙林校区、鼓楼校区和浦口校区。",
  ]
  result = reflect_query(query, context, SYSTEM_PROMPT)
  print(f"Category: {result['category']}")
  print(f"Explanation: {result['explanation']}")
  query = "南京大学的图书馆开放时间是什么时候？"
  context = [
    "67是刘钦",
    "6f是刘峰",
  ]
  result = reflect_query(query, context, SYSTEM_PROMPT)
  print(f"Category: {result['category']}")
  print(f"Explanation: {result['explanation']}")
  query = "石守谦怎么样"
  context = [
    "石守谦是南京大学老师",
    "6f是刘峰",
  ]
  result = reflect_query(query, context, SYSTEM_PROMPT)
  print(f"Category: {result['category']}")
  print(f"Explanation: {result['explanation']}")
