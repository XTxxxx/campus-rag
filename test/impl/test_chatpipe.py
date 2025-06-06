from campus_rag.impl.rag.chat_pipeline import ChatPipeline
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


def test_convstream():
  """
  Test the conversation streaming functionality.
  This is a simple test that runs the pipeline and prints the chunks.
  """
  pipeline = ChatPipeline()
  queries = ["6+是谁？", "有没有事少分高的二层次英语课？"]
  query = queries[1]
  history = []  # Assuming no previous messages for simplicity

  async def run_pipeline():
    async for chunk in pipeline.start(query, history):
      print(chunk)

  import asyncio

  asyncio.run(run_pipeline())
