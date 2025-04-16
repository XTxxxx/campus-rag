from fastapi import FastAPI
from src.campus_rag.api.routes import rag, conversation

app = FastAPI()

app.include_router(rag.router)
app.include_router(conversation.router)