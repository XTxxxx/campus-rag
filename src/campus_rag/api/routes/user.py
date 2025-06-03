from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from campus_rag.domain.rag.vo import ConversationView
from campus_rag.domain.rag.po import SortedBy, ChatMessage
from campus_rag.domain.user.po import User
from campus_rag.domain.user.vo import UserCreate, LoginResponse
import campus_rag.impl.user.conversation as conv_impl
import campus_rag.impl.user.user as user_impl

router = APIRouter()


@router.post(
  "/user/register/", response_model=User, response_description="User created"
)
async def register_user(user: UserCreate) -> User:
  return await user_impl.register_user(user)


@router.post("/user/login/", response_model=LoginResponse, response_description="User's token")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()) -> User:
  return await user_impl.login_user(form_data)


@router.post("/user/create_conversation", response_model=ConversationView)
async def create_conversation(
  current_user: User = Depends(user_impl.get_current_user),
) -> ConversationView:
  return await conv_impl.create_conversation(current_user)


@router.get("/user/conversations", response_model=list[ConversationView])
async def get_conversations(
  user: User = Depends(user_impl.get_current_user),
  first_id: int = 0,
  limit: int = 10,
  sorted_by: SortedBy = SortedBy.updated,
) -> list[ConversationView]:
  return await conv_impl.get_conversations(user, first_id, limit, sorted_by)


@router.get(
  "/user/conversations/{conversation_id}/history",
  response_model=list[ChatMessage],
)
async def get_chat_history(
  conversation_id: str, user: User = Depends(user_impl.get_current_user)
) -> list[ChatMessage]:
  return await conv_impl.get_chat_history(user, conversation_id)
