from fastapi.routing import APIRouter
import src.campus_rag.conversation as inner
from src.campus_rag.conversation import conversation_manager as cm
from src.campus_rag.conversation import ConversationView
from pydantic import UUID4
from typing import List

router = APIRouter()


@router.post("/users", response_model=inner.User, response_description="User created")
def create_user(user_id: str) -> inner.User:
  return cm.create_user(user_id)


@router.post("/users/create_conversation", response_model=inner.Conversation)
def create_conversation(user_id: str) -> inner.Conversation:
  return cm.create_conversation(user_id)


@router.get("/users/{user_id}/conversations", response_model=List[ConversationView])
def get_conversations(
  user_id: str,
  first_id: int = 0,
  limit: int = 10,
  sorted_by: inner.SortedBy = inner.SortedBy.updated,
) -> List[ConversationView]:
  return cm.get_conversations(user_id, first_id, limit, sorted_by)


@router.get(
  "/users/{user_id}/conversations/{conversation_id}/history",
  response_model=list[inner.ChatMessage],
)
def get_chat_history(user_id: str, conversation_id: UUID4) -> list[inner.ChatMessage]:
  return cm.get_chat_history(user_id, conversation_id)
