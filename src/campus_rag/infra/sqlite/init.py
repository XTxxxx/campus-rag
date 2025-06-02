from sqlmodel import SQLModel, create_engine
from campus_rag.constants.sqlite import (
  SQLITE_ASYNC_URL,
  SQLITE_SYNC_URL,
  SQLITE_FILE_NAME,
)
from campus_rag.utils.logging_config import setup_logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import campus_rag.domain.rag.po  # noqa 这里需要导入PO模块以确保SQLModel能够正确识别和创建表结构
import os

log_need_config = __name__ == "__main__"
logger = setup_logger(need_config=log_need_config)


async_engine = create_async_engine(SQLITE_ASYNC_URL, echo=False)
sync_engine = create_engine(SQLITE_SYNC_URL, echo=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


def create_db_and_tables():
  if os.path.exists(SQLITE_FILE_NAME):
    os.remove(SQLITE_FILE_NAME)
  SQLModel.metadata.create_all(sync_engine)


if __name__ == "__main__":
  create_db_and_tables()
  logger.info(f"Database and tables created at {SQLITE_FILE_NAME}")
