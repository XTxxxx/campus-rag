from sqlmodel import SQLModel, create_engine
from campus_rag.constants.sqlite import (
  SQLITE_ASYNC_URL,
  SQLITE_SYNC_URL,
  SQLITE_FILE_NAME,
)
from . import conversation as db
from campus_rag.utils.logging_config import setup_logger
from campus_rag.utils.passwd import get_password_hash
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import campus_rag.domain.user.po as user  # noqa 这里需要导入PO模块以确保SQLModel能够正确识别和创建表结构
import campus_rag.domain.rag.po  # noqa 这里需要导入PO模块以确保SQLModel能够正确识别和创建表结构
import asyncio
import os
import typer

log_need_config = __name__ == "__main__"
logger = setup_logger(need_config=log_need_config)


async_engine = create_async_engine(SQLITE_ASYNC_URL, echo=False)
sync_engine = create_engine(SQLITE_SYNC_URL, echo=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


app = typer.Typer()


@app.command()
def create_db_and_tables():
  if os.path.exists(SQLITE_FILE_NAME):
    os.remove(SQLITE_FILE_NAME)
  SQLModel.metadata.create_all(sync_engine)
  logger.info(f"Database and tables created at {SQLITE_FILE_NAME}")


@app.command()
def add_admin(username: str, password: str) -> bool:
  """Creates an admin user in the database."""
  db_user = asyncio.run(db.find_user_by_name(username))
  if db_user:
    logger.warning(f"User {username} already exists. Skipping creation.")
    return False

  new_user = user.User(
    username=username,
    passwd=get_password_hash(password),
    is_admin=True,
  )

  asyncio.run(db.insert_user(new_user))
  return True


if __name__ == "__main__":
  app()
