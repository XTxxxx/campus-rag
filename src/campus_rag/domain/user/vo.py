from pydantic import BaseModel


class UserCreate(BaseModel):
  username: str
  password: str


class UserView(BaseModel):
  id: int
  username: str

  model_config = {
    "from_attributes": True,
  }


class LoginResponse(BaseModel):
  access_token: str
  token_type: str
  is_admin: bool


class TokenData(BaseModel):
  username: str | None = None
