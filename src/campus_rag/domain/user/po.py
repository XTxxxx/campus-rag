from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
  from ..rag.po import Conversation


class User(SQLModel, table=True):
  id: int = Field(primary_key=True, nullable=False, index=True, unique=True)
  username: str = Field(nullable=False, index=True, unique=True)
  passwd: str = Field(nullable=False)
  create_time: float = Field(default_factory=time.time, nullable=False)
  conversations: list["Conversation"] = Relationship(back_populates="user")
  is_admin: bool = Field(default=False, nullable=False)
