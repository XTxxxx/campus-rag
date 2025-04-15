from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.campus_rag.rag.pipeline import RAGPipeline
from typing import Generator

router = APIRouter()


@router.post("/query")
async def start_rag_pipeline(query: str) -> StreamingResponse:
  rag_pipeline = RAGPipeline()

  return StreamingResponse(rag_pipeline.start(query), media_type="text/event-stream")
