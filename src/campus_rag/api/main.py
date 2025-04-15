from fastapi import FastAPI
from src.campus_rag.api.routes import rag

app = FastAPI()

app.include_router(rag.router)