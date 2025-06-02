import logging
import asyncio
import uuid
from typing import Any, AsyncGenerator
from campus_rag.constants.conversation import ANSWER_PREFIX
from campus_rag.domain.rag.po import Query
from campus_rag.domain.user.po import User
from ..user.conversation import add_message_to_conversation, get_conversation_by_id
from .conv_pipeline import ConverstaionPipeline

logger = logging.getLogger(__name__)
# Task map from task id to task information (queue).
# TODO: add a lock here
_task_dict: dict[str, dict[str, Any]] = {}


async def run_pipeline_and_queue_results(task_id: str, query: str, history: list):
  """Runs the RAG pipeline and puts results into the task's queue."""
  conv_pipeline = ConverstaionPipeline()
  metainfo = ""
  try:
    async for chunk in conv_pipeline.start(query, history):
      # logger.debug(f"Chunk received: {chunk}")
      metainfo = metainfo + chunk
      await _task_dict[task_id]["queue"].put(chunk)
      await asyncio.sleep(0)

    await _task_dict[task_id]["queue"].put(None)
    _task_dict[task_id]["status"] = "completed"
  except Exception as e:
    _task_dict[task_id]["status"] = "error"
    _task_dict[task_id]["error_message"] = str(e)
    # Signal error completion
    await _task_dict[task_id]["queue"].put(None)
    return

  # Persist the final answer
  final_answer = metainfo.split(ANSWER_PREFIX)[-1].strip()
  user = _task_dict[task_id]["user"]
  conversation_id = _task_dict[task_id]["conversation_id"]
  await add_message_to_conversation(
    user,
    conversation_id,
    content=final_answer,
    role="assistant",
    metainfo=metainfo,
  )


async def start_pipeline(query: Query, user: User):
  """
  Starts the RAG pipeline in the background and returns a task ID.
  """
  # Add user message immediately

  task_id = str(uuid.uuid4())
  conversation = await get_conversation_by_id(user, query.conversation_id)
  history = conversation.messages
  await add_message_to_conversation(
    user, query.conversation_id, content=query.query, role="user"
  )

  # Create a queue for this task
  result_queue = asyncio.Queue()
  _task_dict[task_id] = {
    "queue": result_queue,
    "status": "running",
    "error_message": None,
    "user": user,  # Store context for adding assistant message later
    "conversation_id": query.conversation_id,
  }

  # Start the pipeline in the background
  asyncio.create_task(run_pipeline_and_queue_results(task_id, query.query, history))

  return task_id


def task_exists(task_id: str) -> bool:
  """
  Checks if a task with the given ID exists.
  """
  return task_id in _task_dict and (
    _task_dict[task_id]["status"] == "running"
    or _task_dict[task_id]["status"] == "completed"
  )


async def get_rag_stream(task_id: int) -> AsyncGenerator:
  """
  Streams the results of a running RAG pipeline task using SSE.
  """
  task_info = _task_dict[task_id]
  result_queue = task_info["queue"]
  while True:
    chunk = await result_queue.get()
    # logger.debug("---- Chunk sent!!! ----")
    if chunk is None:
      if task_info["status"] == "error":
        yield f"Error: {task_info.get('error_message', 'Unknown error')}"
      break
    yield chunk
