from fastapi.routing import APIRouter
import campus_rag.impl.conversation as conv_sqlite
from pydantic import UUID4
from campus_rag.domain.rag.vo import ConversationView
from campus_rag.domain.rag.po import User, SortedBy, ChatMessage

router = APIRouter()


@router.post("/users", response_model=User, response_description="User created")
async def create_user(user_id: str) -> User:
  return await conv_sqlite.create_user(user_id)


@router.post("/users/create_conversation", response_model=ConversationView)
async def create_conversation(user_id: str) -> ConversationView:
  return await conv_sqlite.create_conversation(user_id)


@router.get("/users/{user_id}/conversations", response_model=list[ConversationView])
async def get_conversations(
  user_id: str,
  first_id: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated,
) -> list[ConversationView]:
  return await conv_sqlite.get_conversations(user_id, first_id, limit, sorted_by)


@router.get(
  "/users/{user_id}/conversations/{conversation_id}/history",
  response_model=list[ChatMessage],
)
async def get_chat_history(user_id: str, conversation_id: str) -> list[ChatMessage]:
  return await conv_sqlite.get_chat_history(user_id, conversation_id)
