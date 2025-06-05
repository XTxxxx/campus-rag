import pytest
from campus_rag.utils.logging_config import setup_logger
from campus_rag.impl.rag.llm_tool.route import route_query

logger = setup_logger()


@pytest.mark.asyncio
async def test_route_query():
  query = "我有门课没通过怎么办？"

  response = await route_query(query)
  logger.info(f"Response: {response}")
  assert isinstance(response, list), "Response should be a list."
  assert response, "Response should not be empty."
