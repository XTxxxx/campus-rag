from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.campus_rag.rag.pipeline import RAGPipeline

import src.campus_rag.conversation as conv_service

cm = conv_service.conversation_manager

router = APIRouter()


@router.post("/query")
async def start_rag_pipeline(query: conv_service.Query) -> StreamingResponse:
  conversation = cm.get_converstaion_by_id(query.user_id, query.conversation_id)
  history = conversation.messages
  cm.add_message(query.user_id, query.conversation_id, "user", query.query)

  rag_pipeline = RAGPipeline()

  async def event_stream() -> AsyncGenerator:
    async for chunk in rag_pipeline.start(query.query, history):
      if chunk.startswith("final answer:"):
        final_answer = chunk.split("final answer:")[-1].strip()
        cm.add_message(
          query.user_id,
          query.conversation_id,
          "assistant",
          final_answer,
        )
        break
      yield chunk

  return StreamingResponse(event_stream(), media_type="text/event-stream")
