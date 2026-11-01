from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel

""" author model """
class AuthorBase (SQLModel):
    fullname: str
    email: EmailStr | None

class Author(AuthorBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    secret_name: str

class AuthorPublic(AuthorBase):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)

class AuthorCreate(AuthorBase):
    secret_name: str

class AuthorUpdate(AuthorBase):
    fullname: str | None = None
    email: EmailStr | None = None
    secret_name: str | None = None

""" user model """
class UserBase(SQLModel):
    username: str
    email: EmailStr | None = None
    fullname: str | None = None

class User(UserBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    password: str

class UserPublic(UserBase):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    username: str | None = None
    email: EmailStr | None = None
    fullname: str | None = None
    password: str | None = None


""" token model """
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None