from pydantic import UUID4
from campus_rag.domain.rag.po import User, Conversation, ChatMessage, SortedBy
from campus_rag.domain.rag.vo import ConversationView
from campus_rag.infra.sqlite import conversation as conversation_db
from fastapi import HTTPException
from typing import Optional
from campus_rag.utils.llm import llm_chat_async
import logging

logger = logging.getLogger(__name__)


async def get_user_by_id(user_id: str) -> Optional[User]:
  """Fetches a user by user_id from the database."""
  db_user = await conversation_db.find_user_by_id(user_id)
  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")
  return db_user


async def create_user(user_id: str) -> User:
  """Creates a new user in the database."""
  db_user = await conversation_db.find_user_by_id(user_id)
  if db_user:
    return db_user
    # raise HTTPException(status_code=409, detail="User already exists")

  return await conversation_db.insert_user(user_id)


async def create_conversation(user_id: str) -> ConversationView:
  """Creates a new conversation for a user."""
  await get_user_by_id(user_id)  # Ensure user exists
  return ConversationView.fromVO(await conversation_db.insert_conversation(user_id))


async def get_conversation_by_id(
  user_id: str, conversation_id: str | UUID4
) -> Conversation:
  """Fetches a specific conversation for a user, including its messages."""

  await get_user_by_id(user_id)
  conversation = await conversation_db.find_conversation_by_id(user_id, conversation_id)
  if not conversation:
    raise HTTPException(status_code=404, detail="Conversation not found")

  return conversation


async def get_conversations(
  user_id: str,
  offset: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated_reverse,
) -> list[ConversationView]:
  """Fetches a list of conversations for a user with sorting and pagination."""
  await get_user_by_id(user_id)  # Ensure user exists

  try:
    conversations = await conversation_db.find_conversations_by_user(
      user_id, offset, limit, sorted_by
    )
    return [ConversationView.fromVO(conv) for conv in conversations]
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


async def get_chat_history(user_id: str, conversation_id: str) -> list[ChatMessage]:
  """Fetches the chat messages for a specific conversation."""
  conversation = await get_conversation_by_id(user_id, conversation_id)
  return await conversation_db.find_messages_by_conversation(
    conversation.conversation_id
  )


async def extract_title_from_content(content: str) -> str:
  """Extract a title from the user's first message using LLM."""
  prompt = [
    {
      "role": "system",
      "content": "You are a helpful assistant. Please generate a concise title for this conversation based on the user's first message. Return only the title without any additional text, quotes or explanations.",
    },
    {"role": "user", "content": f"Generate a title for: {content}"},
  ]

  try:
    title = await llm_chat_async(prompt)
    # Remove any quotes if the LLM added them
    title = title.strip("\"'")
    # Limit length if needed
    if len(title) > 50:
      title = title[:47] + "..."
    return title
  except Exception as e:
    # If title extraction fails, use a fallback
    return content[:20] + "..." if len(content) > 20 else content


async def add_message_to_conversation(
  user_id: str,
  conversation_id: str,
  content: str,
  role: str,
  metainfo: Optional[str] = None,
) -> ChatMessage:
  """Adds a new message to a conversation."""

  new_message = await conversation_db.insert_message(
    conversation_id, content, role, metainfo=metainfo
  )

  conversation = await get_conversation_by_id(user_id, conversation_id)

  # Generate title if it's the first user message and no title exists
  if role == "user" and len(conversation.messages) == 1 and conversation.title is None:
    title = await extract_title_from_content(content)
    conversation.title = title
    logger.debug(
      f"Generated title for conversation {conversation.conversation_id}: {title}"
    )
    await conversation_db.update_conversation(conversation)

  await conversation_db.update_conversation_time(conversation.conversation_id)

  return new_message
