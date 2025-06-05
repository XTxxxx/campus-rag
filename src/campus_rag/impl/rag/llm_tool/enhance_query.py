import logging
from campus_rag.utils.keyword_explain import get_keyword_explain
from campus_rag.utils.llm import llm_chat_async

logger = logging.getLogger(__name__)


async def enhance_query(query: str, keyword_path: str) -> str:
  """
  Enhance the query using keywords from a file.
  :param query: The original query.
  :param keyword_path: Path to the keyword file.
  :return: The enhanced query.
  """
  logger.info("Enhancing query...")

  keyword_str = get_keyword_explain(keyword_path)
  prompt_content = {
    "role": "user",
    "content": f"""
    ## Instruction ##
    根据以下关键词和它们的解释，增强用户的查询。如果用户的问题中包含相关的关键词，提供他们的解释到问题中，否则不要添加任何解释。
    增强查询时不要增加添加无关的信息，不能改变查询原本的意思。
    ## Keywords and Explanations ##
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
