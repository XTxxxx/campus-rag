from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from campus_rag.domain.rag.po import User, Conversation, ChatMessage, SortedBy
from fastapi import HTTPException
from typing import Optional
import logging
import time
import uuid

logger = logging.getLogger(__name__)


async def get_user_by_id(user_id: str, session: AsyncSession) -> Optional[User]:
  """Fetches a user by user_id from the database."""
  statement = select(User).where(User.user_id == user_id)
  result = await session.exec(statement)
  db_user = result.first()
  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")
  return db_user


async def create_user(user_id: str, session: AsyncSession) -> User:
  """Creates a new user in the database."""
  statement = select(User).where(User.user_id == user_id)
  result = await session.exec(statement)
  db_user = result.first()
  if db_user:
    raise HTTPException(status_code=409, detail="User already exists")  # 409 Conflict

  new_user = User(user_id=user_id, create_time=time.time())
  session.add(new_user)
  await session.commit()
  await session.refresh(new_user)
  return new_user


async def create_conversation(user_id: str, session: AsyncSession) -> Conversation:
  """Creates a new conversation for a user."""
  await get_user_by_id(user_id, session)  # Ensure user exists

  new_conversation = Conversation(
    user_id=user_id,
    create_time=time.time(),
    update_time=time.time(),
    title=None,  # Default title can be set later
  )
  session.add(new_conversation)
  await session.commit()
  await session.refresh(new_conversation)
  return new_conversation


async def get_conversation_by_id(
  user_id: str, conversation_id_str: str, session: AsyncSession
) -> Conversation:
  """Fetches a specific conversation for a user, including its messages."""
  try:
    conv_id_uuid = uuid.UUID(conversation_id_str)
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid conversation_id format")

  await get_user_by_id(user_id, session)

  statement = (
    select(Conversation)
    .where(Conversation.conversation_id == conv_id_uuid)
    .where(Conversation.user_id == user_id)
  )
  result = await session.exec(statement)
  conversation = result.first()
  if not conversation:
    raise HTTPException(status_code=404, detail="Conversation not found")
  # Accessing conversation.messages will trigger a load if not already loaded by relationship config
  # print(f"Messages loaded for conversation {conversation.conversation_id}: {len(conversation.messages)}")
  return conversation


async def get_conversations(
  user_id: str,
  session: AsyncSession,
  offset: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated_reverse,  # Default to newest updated
) -> list[Conversation]:
  """Fetches a list of conversations for a user with sorting and pagination."""
  # Ensure user exists
  await get_user_by_id(user_id, session)

  statement = select(Conversation).where(Conversation.user_id == user_id)

  # Apply sorting
  sort_column_name = sorted_by.value
  descending = False
  if sort_column_name.startswith("-"):
    descending = True
    sort_column_name = sort_column_name[1:]

  sort_column = getattr(Conversation, sort_column_name, None)
  if sort_column is None:
    raise HTTPException(status_code=400, detail="Invalid sort key")

  if descending:
    statement = statement.order_by(sort_column.desc())
  else:
    statement = statement.order_by(sort_column.asc())

  # Apply pagination
  statement = statement.offset(offset).limit(limit)

  result = await session.exec(statement)
  conversations = result.all()
  # For each conversation, messages can be loaded upon access due to the Relationship setup.
  # If you need to ensure all messages are pre-loaded for all conversations in the list:
  # for conv in conversations:
  #     _ = conv.messages # Access to trigger lazy load, or use eager loading options in the select
  return conversations


async def get_chat_history(
  user_id: str, conversation_id_str: str, session: AsyncSession
) -> list[ChatMessage]:
  """Fetches the chat messages for a specific conversation."""
  # This reuses get_conversation_by_id_db which already loads messages
  conversation = await get_conversation_by_id(user_id, conversation_id_str, session)
  return (
    conversation.messages
  )  # Messages are ordered by create_time due to relationship config


async def add_message_to_conversation(
  user_id: str, conversation_id_str: str, content: str, role: str, session: AsyncSession
) -> ChatMessage:
  """Adds a new message to a conversation."""
  conversation = await get_conversation_by_id(user_id, conversation_id_str, session)

  new_message = ChatMessage(
    conversation_id=conversation.conversation_id,
    role=role,
    content=content,
    create_time=time.time(),
  )

  conversation.append_message(new_message)
  session.add(new_message)
  await session.commit()
  await session.refresh(new_message)

  return new_message
