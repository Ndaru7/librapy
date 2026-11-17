from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import SQLModel, engine, get_session, init_db
from app.models import (
    Author,
    AuthorCreate,
    AuthorPublic,
    AuthorUpdate,
    Token,
    TokenData,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"


app = FastAPI(lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/author/view/{author_id}", response_model=AuthorPublic)
async def retrieve_author(
    author_id: Annotated[UUID, Path()],
    session: SessionDep
):
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@app.get("/author/view/", response_model=list[AuthorPublic])
async def view_author(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
):
    author = session.exec(select(Author).offset(offset).limit(limit)).all()
    return author

@app.post("/author/add", response_model=AuthorPublic)
async def add_author(
    author: Annotated[AuthorCreate, Query()],
    session: SessionDep
):
    val_author = Author.model_validate(author)
    session.add(val_author)
    session.commit()
    session.refresh(val_author)
    return val_author

@app.patch("/author/update/{author_id}", response_model=AuthorPublic)
def update_author(
    author_id: Annotated[UUID, Path()],
    author: AuthorUpdate,
    session: SessionDep
):
    val_author = session.get(Author, author_id)
    if not val_author:
        raise HTTPException(status_code=404, detail="Author not found")
    data_author = author.model_dump(exclude_unset=True)
    val_author.sqlmodel_update(data_author)
    session.add(val_author)
    session.commit()
    session.refresh(val_author)
    return val_author

@app.delete("/author/delete/{author_id}")
async def delete_author(
    author_id: Annotated[UUID, Path()],
    session: SessionDep
):
	author = session.get(Author, author_id)
	if not author:
		raise HTTPException(status_code=404, detail="Author not found")
	session.delete(author)
	session.commit()
	return {"ok": True}

@app.get("/user/view/{user_id}", response_model=UserPublic)
async def retrieve_user(
    user_id: Annotated[str, Path()],
    session: SessionDep
):
    user = session.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/user/view/", response_model=list[UserPublic])
async def view_user(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
):
    user = session.exec(select(User).offset(offset).limit(limit)).all()
    return user

@app.post("/user/add", response_model=UserPublic)
async def add_user(
    user: Annotated[UserCreate, Query()],
    session: SessionDep
):
    val_user = User.model_validate(user)
    session.add(val_user)
    session.commit()
    session.refresh(val_user)
    return val_user

@app.patch("/user/update/{user_id}", response_model=UserPublic)
def update_user(
    user_id: Annotated[UUID, Path()],
    user: UserUpdate,
    session: SessionDep
):
    val_user = session.get(User, user_id)
    if not val_user:
        raise HTTPException(status_code=404, detail="User not found")
    data_user = user.model_dump(exclude_unset=True)
    val_user.sqlmodel_update(data_user)
    session.add(val_user)
    session.commit()
    session.refresh(val_user)
    return val_user

@app.delete("/user/delete/{user_id}")
async def delete_user(
    user_id: Annotated[UUID, Path()],
    session: SessionDep
):
	user = session.get(User, user_id)
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	session.delete(user)
	session.commit()
	return {"ok": True}

def get_user(username: str):
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        result  = session.exec(query).one()
        return result

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        password_hash.verify(password, DUMMY_HASH)
    if not password_hash.verify(password, DUMMY_HASH):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exeption = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exeption
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exeption
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exeption
    return user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    val_user = authenticate_user(form_data.username, form_data.password)
    if not val_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(form_data.username)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    print(access_token)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

@app.get("/users/me/items")
async def read_own_items(current_user: Annotated[User, Depends(get_current_user)]):
    return [{"item_id": "foo", "owner": current_user.username}]