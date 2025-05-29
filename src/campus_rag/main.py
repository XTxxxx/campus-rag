from campus_rag.utils.logging_config import setup_logger

logger = setup_logger()
from campus_rag.api.routes import rag, conversation, course_scheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse

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
app.include_router(course_scheduler.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
  logger.error(f"Validation error: {exc.errors()}")
  return JSONResponse(
    status_code=422,
    content={"detail": exc.errors(), "body": exc.body},
  )
