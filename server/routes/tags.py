from typing import Annotated

import db
from db.models import Tags
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils.requests import RouteRequest

router = APIRouter(tags=["Tags"])


@router.get("/tags")
async def list_tags(
    request: RouteRequest, db: Annotated[AsyncSession, Depends(db.use)]
):
    return (await db.exec(select(Tags).order_by(desc(Tags.name)))).all()


class TagCreateResponse(BaseModel):
    name: str
    description: str


@router.post("/tags/create")
async def create_tag(
    request: RouteRequest,
    req: TagCreateResponse,
    *,
    db: Annotated[AsyncSession, Depends(db.use)],
):
    async with db.begin_nested():
        tag = Tags(**req.model_dump())
        db.add(tag)

    await db.commit()
    await db.refresh(tag)
    return tag


@router.post("/tags/bulk-create")
async def bulk_create_tags(
    request: RouteRequest,
    req: list[TagCreateResponse],
    *,
    db: Annotated[AsyncSession, Depends(db.use)],
):
    async with db.begin_nested():
        created_tags = [Tags(**tag.model_dump()) for tag in req]
        db.add_all(created_tags)

    await db.commit()
    return created_tags
