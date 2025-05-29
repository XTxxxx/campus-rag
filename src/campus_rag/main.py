from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from campus_rag.api.routes import rag, conversation

origins = ["*"]

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
