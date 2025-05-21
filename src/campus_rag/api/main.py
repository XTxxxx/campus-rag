from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.campus_rag.api.routes import rag, conversation
from src.campus_rag.utils.logging_config import setup_logger

origins = ["*"]

logger = setup_logger("debug")
app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(rag.router)
app.include_router(conversation.router)
