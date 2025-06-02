from pydantic import UUID4
from campus_rag.domain.rag.po import Conversation, ChatMessage, SortedBy
from campus_rag.domain.rag.vo import ConversationView
from campus_rag.domain.user.po import User
from campus_rag.infra.sqlite import conversation as db
from fastapi import HTTPException
from typing import Optional
from campus_rag.utils.llm import llm_chat_async
import logging

logger = logging.getLogger(__name__)


async def create_conversation(user: User) -> ConversationView:
  """Creates a new conversation for a user."""
  return ConversationView.fromVO(await db.insert_conversation(user.id))


async def get_conversation_by_id(
  user: User, conversation_id: str | UUID4
) -> Conversation:
  """Fetches a specific conversation for a user, including its messages."""

  conversation = await db.find_conversation_by_id(user.id, conversation_id)
  if not conversation:
    raise HTTPException(status_code=404, detail="Conversation not found")

  return conversation


async def get_conversations(
  user: User,
  offset: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated_reverse,
) -> list[ConversationView]:
  """Fetches a list of conversations for a user with sorting and pagination."""
  try:
    conversations = await db.find_conversations_by_user(
      user.id, offset, limit, sorted_by
    )
    return [ConversationView.fromVO(conv) for conv in conversations]
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


async def get_chat_history(user: User, conversation_id: str) -> list[ChatMessage]:
  """Fetches the chat messages for a specific conversation."""
  conversation = await get_conversation_by_id(user, conversation_id)
  return await db.find_messages_by_conversation(conversation.conversation_id)


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
  user: User,
  conversation_id: str,
  content: str,
  role: str,
  metainfo: Optional[str] = None,
) -> ChatMessage:
  """Adds a new message to a conversation."""

  new_message = await db.insert_message(
    conversation_id, content, role, metainfo=metainfo
  )

  conversation = await get_conversation_by_id(user, conversation_id)

  # Generate title if it's the first user message and no title exists
  if role == "user" and len(conversation.messages) == 1 and conversation.title is None:
    title = await extract_title_from_content(content)
    conversation.title = title
    logger.debug(
      f"Generated title for conversation {conversation.conversation_id}: {title}"
    )
    await db.update_conversation(conversation)

  await db.update_conversation_time(conversation.conversation_id)

  return new_message
