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


app = FastAPI(lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]


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
    user_id: Annotated[UUID, Path()],
    session: SessionDep
):
    user = session.get(User, user_id)
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
    user: AuthorUpdate,
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