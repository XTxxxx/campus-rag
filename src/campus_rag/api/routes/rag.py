import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from campus_rag.domain.rag.po import Query
from campus_rag.domain.rag.vo import TaskResponse
from campus_rag.impl.rag.pipeline_entry import (
  start_pipeline,
  get_rag_stream,
  task_exists,
)
from campus_rag.impl.user.user import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/query", response_model=TaskResponse)
async def start_rag_pipeline_task(
  query: Query, user: str = Depends(get_current_user)
) -> JSONResponse:
  return JSONResponse(content={"task_id": await start_pipeline(query, user)})


@router.get(
  "/stream/{task_id}",
  response_class=StreamingResponse,
  responses={
    200: {
      "content": {"text/event-stream": {}},
      "description": "Stream RAG results using Server-Sent Events (SSE)",
    },
    404: {"description": "Task not found"},
  },
)
async def stream_rag_pipeline_results(task_id: str) -> StreamingResponse:
  if not task_exists(task_id):
    raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found.")

  async def event_stream() -> AsyncGenerator[str, None]:
    try:
      async for chunk in get_rag_stream(task_id):
        if chunk is None:
          break
        yield f"data: {chunk}\n\n"
      yield "data: [DONE]\n\n"  # Signal end of stream
    except asyncio.CancelledError:
      raise
    finally:
      # Optional: More robust cleanup?
      # Be careful removing the task entry here if multiple clients could stream
      pass

  return StreamingResponse(event_stream(), media_type="text/event-stream")
