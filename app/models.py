from uuid import UUID, uuid4

from pydantic import EmailStr
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

