from typing import Annotated

import db
from db.models import Tags
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import desc, select
from utils.types import Database

router = APIRouter(tags=["Tags"])


@router.get("/tags")
async def list_tags(db: Annotated[Database, Depends(db.use)]):
    return (await db.exec(select(Tags).order_by(desc(Tags.name)))).all()


class TagCreateResponse(BaseModel):
    name: str
    description: str


@router.post("/tags/create")
async def create_tag(
    req: TagCreateResponse,
    *,
    db: Annotated[Database, Depends(db.use)],
):
    async with db.begin_nested():
        tag = Tags(**req.model_dump())
        db.add(tag)

    await db.commit()
    await db.refresh(tag)
    return tag


@router.post("/tags/bulk-create")
async def bulk_create_tags(
    req: list[TagCreateResponse],
    *,
    db: Annotated[Database, Depends(db.use)],
):
    async with db.begin_nested():
        created_tags = [Tags(**tag.model_dump()) for tag in req]
        db.add_all(created_tags)

    await db.commit()
    return created_tags
