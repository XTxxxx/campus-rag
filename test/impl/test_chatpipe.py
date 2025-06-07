from campus_rag.impl.rag.chat_pipeline import ChatPipeline
from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()


def test_chatpipe():
  """
  Test the conversation streaming functionality.
  This is a simple test that runs the pipeline and prints the chunks.
  """
  pipeline = ChatPipeline()
  queries = ["6+是谁？", "有没有事少分高的二层次英语课？", "你好", "成绩不合格的课程如何补考？", "课程成绩申诉的有效时限是多久？"]
  query = queries[-1]
  history = []  # Assuming no previous messages for simplicity

  async def run_pipeline():
    async for chunk in pipeline.start(query, history):
      print(chunk)

  import asyncio

  asyncio.run(run_pipeline())
