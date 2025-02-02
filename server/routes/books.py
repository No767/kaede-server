import uuid
from typing import TYPE_CHECKING, Annotated

import db
from db.models import Book, Tags
from fastapi import APIRouter, Depends
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlmodel import desc, select
from utils.pages import KaedePages, KaedeParams
from utils.responses import OkResponse
from utils.sessions import authorize

if TYPE_CHECKING:
    from utils.types import Database

router = APIRouter(tags=["books"])


@router.get("/books")
async def get_books(
    db: Annotated[Database, Depends(db.use)],
    *,
    params: Annotated[KaedeParams, Depends()],
) -> KaedePages[Book]:
    """Get a paginated list of books"""
    query = select(Book).order_by(desc(Book.created_at))
    return await paginate(db, query, params)


@router.get("/books/{id}")
async def get_book(id: uuid.UUID, *, db: Annotated[Database, Depends(db.use)]) -> Book:
    """Gets information about a book specified via ID"""
    return (await db.exec(select(Book).where(Book.id == id))).one()


class EditBookResponse(BaseModel):
    title: str
    description: str


@router.patch("/books/{id}")
async def edit_book(
    id: uuid.UUID,
    req: EditBookResponse,
    *,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
) -> Book:
    book = (
        await db.exec(select(Book).where(Book.id == id).where(Book.owner == me_id))
    ).one()
    for key, value in req.model_dump().items():
        setattr(book, key, value)

    await db.refresh(book)
    return book


@router.delete("/books/{id}")
async def delete_book(
    id: uuid.UUID,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
):
    await db.delete(select(Book).where(Book.id == id).where(Book.owner == me_id))
    return OkResponse()


class CreateBookResponse(BaseModel):
    title: str
    description: str
    author: int
    tags: list[str]


@router.post("/books/create")
async def create_book(
    req: CreateBookResponse,
    *,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
) -> Book:
    async with db.begin_nested():
        book = Book(owner=me_id, **req.model_dump(exclude={"tags": False}))
        db.add(book)
        db.add_all(
            [
                (await db.exec(select(Tags).where(Tags.name == tag))).one()
                for tag in req.tags
            ]
        )

    await db.commit()
    await db.refresh(book)
    return book
