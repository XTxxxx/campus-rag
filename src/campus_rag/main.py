from campus_rag.domain.course.po import ScheduleError
from campus_rag.utils.logging_config import setup_logger
from campus_rag.constants.log import LOG_FILE_PATH

logger = setup_logger(log2file=True)
from campus_rag.api.routes import rag, course_scheduler, user, knowledge_base
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import os

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
app.include_router(user.router)
app.include_router(course_scheduler.router)
app.include_router(knowledge_base.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
  logger.error(f"Validation error: {exc.errors()}")
  return JSONResponse(
    status_code=422,
    content={"detail": exc.errors(), "body": exc.body},
  )


@app.exception_handler(ScheduleError)
async def schedule_error_handler(request: Request, exc: ScheduleError):
  logger.error("Schedule error")
  return JSONResponse(
    status_code=400,
    content={"detail": "规划时发生错误，请修改后重试！"},
  )


@app.get("/log")
async def stream_logs():
  async def log_generator():
    if not os.path.exists(LOG_FILE_PATH):
      logger.warning(f"Log file {LOG_FILE_PATH} does not exist.")
      yield "Log file not found.\n"
      return
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
      while True:
        line = f.readline()
        if not line:
          await asyncio.sleep(0.5)
          continue
        yield line  # 注意这里不做 decode，原样输出（包括颜色）

  return StreamingResponse(log_generator(), media_type="text/plain")
