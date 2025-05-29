from campus_rag.impl.rag.conv_pipeline import ConverstaionPipeline


def test_convstream():
  """
  Test the conversation streaming functionality.
  This is a simple test that runs the pipeline and prints the chunks.
  """
  pipeline = ConverstaionPipeline()
  query = "你好"
  history = []  # Assuming no previous messages for simplicity

  async def run_pipeline():
    async for chunk in pipeline.start(query, history):
      print(chunk)

  import asyncio

  asyncio.run(run_pipeline())
