from pydantic import BaseModel
from .po import Conversation
from typing import Optional


class ConversationView(BaseModel):
  conversation_id: str
  title: Optional[str] = None

  @classmethod
  def fromVO(cls, conversation: Conversation) -> "ConversationView":
    """Converts a Conversation object to a ConversationView."""
    return ConversationView(
      conversation_id=conversation.conversation_id,
      title=conversation.title,
    )


class TaskResponse(BaseModel):
  task_id: str
