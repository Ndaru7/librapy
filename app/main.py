from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlmodel import Session, select

from app.database import SQLModel, engine, get_session, init_db
from app.models import Author, AuthorCreate, AuthorPublic, AuthorUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/author/view/{author_id}", response_model=AuthorPublic)
async def retrieve_author(
    author_id: Annotated[UUID, Path()], session: SessionDep
) -> Author:
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.get("/author/view/", response_model=list[AuthorPublic])
async def view_author(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
):
    author = session.exec(select(Author).offset(offset).limit(limit)).all()
    return author


@app.post("/author/add", response_model=AuthorPublic)
async def add_author(author: Annotated[AuthorCreate, Query()], session: SessionDep):
    val_author = Author.model_validate(author)
    session.add(val_author)
    session.commit()
    session.refresh(val_author)
    return val_author

@app.patch("/author/update/{author_id}", response_model=AuthorPublic)
def update_author(author_id: Annotated[UUID, Path()], author: AuthorUpdate, session: SessionDep):
    val_author = session.get(Author, author_id)
    if not val_author:
        raise HTTPException(status_code=404, detail="Autho not found")
    data_author = author.model_dump(exclude_unset=True)
    val_author.sqlmodel_update(data_author)
    session.add(val_author)
    session.commit()
    session.refresh(val_author)
    return val_author

@app.delete("/author/delete/{author_id}")
async def delete_author(author_id: Annotated[UUID, Path()], session: SessionDep):
	author = session.get(Author, author_id)
	if not author:
		raise HTTPException(status_code=404, detail="Author not found")
	session.delete(author)
	session.commit()
	return {"ok": True}