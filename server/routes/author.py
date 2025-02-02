import uuid
from typing import Annotated, Optional

import db
from db.models import Author
from fastapi import APIRouter, Depends
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlmodel import delete, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils.pages import KaedeParams
from utils.responses import OkResponse
from utils.sessions import authorize

from .assets import assert_asset_hash

router = APIRouter(tags=["Authors"])


@router.get("/author")
async def list_authors(
    db: Annotated[AsyncSession, Depends(db.use)],
    *,
    params: Annotated[KaedeParams, Depends()],
):
    query = select(Author).order_by(desc(Author.name))
    return paginate(db, query, params)


@router.get("/author/{id}")
async def get_author(id: uuid.UUID, *, db: Annotated[AsyncSession, Depends(db.use)]):
    return (await db.exec(select(Author).where(Author.id == id))).one()


class EditAuthorResponse(BaseModel):
    name: Optional[str]
    avatar_hash: Optional[str]


@router.patch("/author/{id}")
async def edit_author(
    id: uuid.UUID,
    req: EditAuthorResponse,
    *,
    db: Annotated[AsyncSession, Depends(db.use)],
):
    if req.avatar_hash:
        await assert_asset_hash(db, req.avatar_hash)

    author = (await db.exec(select(Author).where(Author.id == id))).one()

    for key, value in req.model_dump().items():
        match key:
            case "name":
                setattr(author, key, value)
            case "photo_hash":
                pass
            case _:
                setattr(author, key, value)

    new_avatar = req.avatar_hash
    old_avatar = author.avatar_hash

    author.avatar_hash = new_avatar if old_avatar is not new_avatar else old_avatar

    db.add(author)
    await db.commit()
    await db.refresh(author)
    return author


@router.delete("/author/{id}")
async def delete_author(
    id: int,
    *,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[AsyncSession, Depends(db.use)],
):
    await db.delete(delete(Author).where(Author.id == id))  # type: ignore # Pyright is tripping up again...
    return OkResponse()
