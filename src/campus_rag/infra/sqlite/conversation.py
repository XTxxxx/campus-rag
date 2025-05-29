from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from campus_rag.domain.rag.po import (
  User,
  Conversation,
  ChatMessage,
  SortedBy,
  sorted_columns,
)
from typing import Optional
from .init import async_session
import logging
import time
import uuid

logger = logging.getLogger(__name__)


async def find_user_by_id(user_id: str) -> Optional[User]:
  """Finds a user by user_id from the database."""
  async with async_session() as session:
    statement = select(User).where(User.user_id == user_id)
    result = await session.execute(statement)
    return result.scalars().first()


async def insert_user(user_id: str) -> User:
  """Inserts a new user into the database."""
  async with async_session() as session:
    new_user = User(user_id=user_id, create_time=time.time())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def insert_conversation(user_id: str) -> Conversation:
  """Inserts a new conversation into the database."""
  async with async_session() as session:
    new_conversation = Conversation(
      user_id=user_id,
      update_time=time.time(),
      title=None,
    )
    session.add(new_conversation)
    await session.commit()
    await session.refresh(new_conversation)
    return new_conversation


async def find_conversation_by_id(
  user_id: str, conversation_id: uuid.UUID
) -> Optional[Conversation]:
  """Finds a specific conversation by ID and user_id."""
  async with async_session() as session:
    statement = (
      select(Conversation)
      .where(Conversation.conversation_id == conversation_id)
      .where(Conversation.user_id == user_id)
      .options(selectinload(Conversation.messages))
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def find_conversations_by_user(
  user_id: str,
  offset: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated_reverse,
) -> list[Conversation]:
  """Finds conversations for a user with sorting and pagination."""
  async with async_session() as session:
    statement = select(Conversation).where(Conversation.user_id == user_id)

    # Apply sorting
    sort_column_name = sorted_by.value
    descending = sort_column_name.startswith("-")

    sort_column = getattr(Conversation, sorted_columns[sorted_by], None)
    if sort_column is None:
      raise ValueError("Invalid sort key")

    if descending:
      statement = statement.order_by(sort_column.desc())
    else:
      statement = statement.order_by(sort_column.asc())

    statement = statement.offset(offset).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


async def find_messages_by_conversation(
  conversation_id: uuid.UUID,
) -> list[ChatMessage]:
  """Finds all messages for a conversation."""
  async with async_session() as session:
    statement = (
      select(ChatMessage)
      .where(ChatMessage.conversation_id == conversation_id)
      .order_by(ChatMessage.create_time)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def insert_message(
  conversation_id: uuid.UUID, content: str, role: str, metainfo: Optional[str] = None
) -> ChatMessage:
  """Inserts a new message into the database."""
  async with async_session() as session:
    new_message = ChatMessage(
      conversation_id=conversation_id,
      role=role,
      content=content,
      metainfo=metainfo,
    )
    session.add(new_message)
    await session.commit()
    await session.refresh(new_message)
    conversation = (
      (
        await session.execute(
          select(Conversation)
          .where(Conversation.conversation_id == conversation_id)
          .options(selectinload(Conversation.messages))
        )
      )
      .scalars()
      .first()
    )
    await session.refresh(conversation, attribute_names=["messages"])
    return new_message


async def update_conversation_time(conversation_id: uuid.UUID) -> None:
  """Updates the update_time of a conversation."""
  async with async_session() as session:
    statement = select(Conversation).where(
      Conversation.conversation_id == conversation_id
    )
    result = await session.execute(statement)
    conversation = result.scalars().first()
    if conversation:
      conversation.update_time = time.time()
      session.add(conversation)
      await session.commit()


async def update_conversation(conversation: Conversation) -> None:
  """Updates the conversation in the database."""
  async with async_session() as session:
    session.add(conversation)
    await session.commit()
