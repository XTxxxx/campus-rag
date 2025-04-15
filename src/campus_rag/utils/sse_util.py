from typing import AsyncGenerator


async def send_status(status: str, metadata=None) -> AsyncGenerator:
  """
  Send a status update with metadata.
  """
  yield status, metadata
