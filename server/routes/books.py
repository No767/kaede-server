import uuid
from typing import Annotated

import db
from db.models import Book, Tags
from fastapi import APIRouter, Depends
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils.pages import KaedePages, KaedeParams
from utils.responses import OkResponse
from utils.sessions import authorize

router = APIRouter(tags=["books"])


@router.get("/books")
async def get_books(
    db: AsyncSession = Depends(db.use), *, params: Annotated[KaedeParams, Depends()]
) -> KaedePages[Book]:
    """Get a paginated list of books"""
    query = select(Book).order_by(desc(Book.created_at))
    return await paginate(db, query, params)


@router.get("/books/{id}")
async def get_book(id: uuid.UUID, *, db: AsyncSession = Depends(db.use)) -> Book:
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
    db: AsyncSession = Depends(db.use),
    me_id: int = Depends(authorize),
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
    id: uuid.UUID, db: AsyncSession = Depends(db.use), me_id: int = Depends(authorize)
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
    db: AsyncSession = Depends(db.use),
    me_id: int = Depends(authorize),
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
