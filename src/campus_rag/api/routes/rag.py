import asyncio
from curses import meta
import uuid
from typing import AsyncGenerator, Dict, Any
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from src.campus_rag.rag.pipeline import (
  _ANSWER_PREFIX,
  RAGPipeline,
  _FINAL_ANSWER_PREFIX,
)

import src.campus_rag.conversation as conv_service

cm = conv_service.conversation_manager

router = APIRouter()

# Store running tasks and their queues
tasks: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger(__name__)


def extract_final_answer(metainfo: str) -> str:
  """
  Extracts the final answer from the metainfo string.
  """
  # Assuming the final answer is the last part of the metainfo
  return metainfo.split(_ANSWER_PREFIX)[-1].strip().strip("\\n").strip()


async def run_pipeline_and_queue_results(task_id: str, query: str, history: list):
  """Runs the RAG pipeline and puts results into the task's queue."""
  rag_pipeline = RAGPipeline()
  metainfo_stored = False
  try:
    async for chunk in rag_pipeline.start(query, history):
      logger.info(f"Chunk received: {chunk}")
      await tasks[task_id]["queue"].put(chunk)
      # Explicitly yield control to the event loop
      await asyncio.sleep(0)
      if chunk.startswith(_FINAL_ANSWER_PREFIX):
        final_answer = chunk.split(_FINAL_ANSWER_PREFIX)[-1].strip()
        # Store final answer for potential later retrieval if needed
        tasks[task_id]["metainfo"] = final_answer
        tasks[task_id]["final_answer"] = extract_final_answer(final_answer)
        # Mark final answer stored to avoid double storing if stream ends abruptly
        metainfo_stored = True
        # Signal completion by putting a special marker or None
        await tasks[task_id]["queue"].put(None)
        break  # Stop processing after final answer
    # If the loop finishes without finding "final answer:", signal completion
    if not metainfo_stored:
      await tasks[task_id]["queue"].put(None)
    tasks[task_id]["status"] = "completed"
  except Exception as e:
    tasks[task_id]["status"] = "error"
    tasks[task_id]["error_message"] = str(e)
    # Signal error completion
    await tasks[task_id]["queue"].put(None)
  finally:
    # Optional: Add cleanup logic here if needed, e.g., removing the task entry after some time
    pass


@router.post("/query")
async def start_rag_pipeline_task(
  query: conv_service.Query,
) -> JSONResponse:
  """
  Starts the RAG pipeline in the background and returns a task ID.
  """
  task_id = str(uuid.uuid4())
  conversation = cm.get_converstaion_by_id(query.user_id, query.conversation_id)
  history = conversation.messages
  # Add user message immediately
  cm.add_message(query.user_id, query.conversation_id, "user", query.query)

  # Create a queue for this task
  result_queue = asyncio.Queue()
  tasks[task_id] = {
    "queue": result_queue,
    "status": "running",
    "final_answer": None,
    "metainfo": None,
    "error_message": None,
    "user_id": query.user_id,  # Store context for adding assistant message later
    "conversation_id": query.conversation_id,
  }

  # Start the pipeline in the background
  asyncio.create_task(run_pipeline_and_queue_results(task_id, query.query, history))

  return JSONResponse(content={"task_id": task_id})


@router.get("/stream/{task_id}")
async def stream_rag_pipeline_results(task_id: str) -> StreamingResponse:
  """
  Streams the results of a running RAG pipeline task using SSE.
  """
  if task_id not in tasks:
    raise HTTPException(status_code=404, detail="Task not found")

  task_info = tasks[task_id]
  result_queue = task_info["queue"]

  async def event_stream() -> AsyncGenerator[str, None]:
    try:
      while True:
        chunk = await result_queue.get()
        logger.info("---- Chunk sended!!! ----")
        if chunk is None:  # End of stream signal
          # Check if a final answer was generated and store it
          if task_info["status"] == "completed" and task_info["final_answer"]:
            cm.add_message(
              task_info["user_id"],
              task_info["conversation_id"],
              "assistant",
              task_info["final_answer"],
              metainfo=task_info["metainfo"],
            )
          elif task_info["status"] == "error":
            # Optionally yield an error message to the client
            yield f"data: Error: {task_info.get('error_message', 'Unknown error')}\n\n"
          yield "data: [DONE]\n\n"
          break
        if chunk.startswith(_FINAL_ANSWER_PREFIX):
          continue
        yield f"data: {chunk}\n\n"
    except asyncio.CancelledError:
      # Handle client disconnect if necessary
      print(f"Client disconnected for task {task_id}")
      # Optionally update task status or perform cleanup
      task_info["status"] = "disconnected"
      raise
    finally:
      # Optional: More robust cleanup?
      # Be careful removing the task entry here if multiple clients could stream
      pass

  return StreamingResponse(event_stream(), media_type="text/event-stream")
