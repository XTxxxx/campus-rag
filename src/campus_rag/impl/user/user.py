from datetime import timedelta
from operator import is_
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from campus_rag.constants.passwd import ACCESS_TOKEN_EXPIRE_MINUTES
from campus_rag.domain.user.po import User
from campus_rag.domain.user.vo import UserCreate, LoginResponse, TokenData
from campus_rag.infra.sqlite import conversation as db
from campus_rag.utils.passwd import (
  create_access_token,
  get_password_hash,
  verify_password,
)
from campus_rag.constants.passwd import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")


async def get_user_by_name(user_name: str) -> Optional[User]:
  """Fetches a user by user_id from the database."""
  db_user = await db.find_user_by_name(user_name)
  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")
  return db_user


async def register_user(user_create: UserCreate) -> User:
  """Creates a new user in the database."""
  db_user = await db.find_user_by_name(user_create.username)
  if db_user:
    raise HTTPException(status_code=409, detail="User already exists")

  new_user = User(
    username=user_create.username,
    passwd=get_password_hash(user_create.password),
  )

  await db.insert_user(new_user)
  return new_user


async def login_user(login_form: OAuth2PasswordRequestForm) -> LoginResponse:
  user = await db.find_user_by_name(login_form.username)
  if not user or not verify_password(login_form.password, user.passwd):
    raise HTTPException(
      status_code=401,
      detail="Invalid username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )

  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": user.username}, expires_delta=access_token_expires
  )
  return LoginResponse(
    access_token=access_token, token_type="bearer", is_admin=user.is_admin
  )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
  credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise credentials_exception
    token_data = TokenData(username=username)
  except JWTError:
    raise credentials_exception
  user = await db.find_user_by_name(username=token_data.username)
  if user is None:
    raise credentials_exception
  return user


async def get_current_admin_user(
  current_user: User = Depends(get_current_user),
) -> User:
  """Ensures the current user is an admin.
  To add an admin user, use the `add_admin` command in the SQLite init script.
  """
  if not current_user.is_admin:
    raise HTTPException(
      status_code=403, detail="You do not have permission to perform this action."
    )
  return current_user
