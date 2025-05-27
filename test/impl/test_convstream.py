from campus_rag.impl.rag.conv_pipeline import ConverstaionPipeline


if __name__ == "__main__":
  import asyncio

  async def main():
    pipeline = ConverstaionPipeline()
    query = "你好"
    history = []  # Assuming no previous messages for simplicity
    async for chunk in pipeline.start(query, history):
      print(chunk)

  asyncio.run(main())
