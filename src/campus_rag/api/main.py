from fastapi import FastAPI
from src.campus_rag.api.routes import rag, conversation
from src.campus_rag.utils.logging_config import configure_logger

logger = configure_logger()

logger.info("Starting FastAPI application...")
app = FastAPI()

app.include_router(rag.router)
app.include_router(conversation.router)
