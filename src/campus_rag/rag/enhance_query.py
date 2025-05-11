import logging
import json
from functools import reduce
from src.campus_rag.utils.llm import llm_chat_async

logger = logging.getLogger(__name__)


def _construct_keyword_explanation(keyword_path: str) -> str:
  with open(keyword_path, "r") as f:
    data = json.load(f)
  return reduce(
    lambda x, y: x + "\n" + y,
    [f"{item['keyword']} 的解释是: {item['explanation']}" for item in data],
  )


async def enhance_query(query: str, keyword_path: str) -> str:
  """
  Enhance the query using keywords from a file.
  :param query: The original query.
  :param keyword_path: Path to the keyword file.
  :return: The enhanced query.
  """
  logger.info("Enhancing query...")

  keyword_str = _construct_keyword_explanation(keyword_path)
  prompt_content = {
    "role": "user",
    "content": f"""
    ## Instruction ##
    Enhance usr's query according to the following keywords and their explanations.
    Only output the enhanced query, do not add any other content.
    {keyword_str}
    ## Query ##
    {query}
    """,
  }
  enhanced_query = await llm_chat_async([prompt_content])
  logger.info("Enhanced query: %s", enhanced_query)
  return enhanced_query


if __name__ == "__main__":
  # Example usage
  query = "南哪是985吗？"
  keyword_path = "data/keywords.json"
  enhanced_query = enhance_query(query, keyword_path)
  print(enhanced_query)
