from campus_rag.utils.keyword_explain import get_keyword_explain
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


def test_keyword_explain():
  result = get_keyword_explain("data/keywords.json")
  logger.info(f"Keyword explain result: {result}")


def test_schedule_keyword_explain():
  result = get_keyword_explain("data/keywords_for_schedule.json")
  logger.info(f"Course keyword explain result: {result}")
