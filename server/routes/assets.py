import io
from typing import Annotated, Any, Optional

import db
from db.models import (
    Asset,
)
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils.assets import hash_bytes
from utils.sessions import authorize

UPLOAD_LIMIT = 1024 * 1024 * 5  # 5 MB

router = APIRouter(tags=["assets"])


@router.get(
    "/assets/{asset_hash}",
    responses={
        200: {
            "content": {
                "application/octet-stream": {},
                "application/json": None,
            },
            "description": "Return the bytes of the asset in body",
        }
    },
)
async def get_asset(
    asset_hash: str,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[AsyncSession, Depends(db.use)],
) -> StreamingResponse:
    """
    This function returns an asset by hash.
    """

    asset = (await db.exec(select(Asset).where(Asset.hash == asset_hash))).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Not found")

    stream = io.BytesIO(asset.data)
    return StreamingResponse(stream, media_type=asset.content_type)


class GetAssetMetadataResponse(BaseModel):
    content_type: str
    alt: str | None = None


@router.get("/assets/{asset_hash}/metadata")
async def get_asset_metadata(
    asset_hash: str,
    db: Annotated[AsyncSession, Depends(db.use)],
    me: str = Depends(authorize),
) -> GetAssetMetadataResponse:
    """
    This function returns metadata for an asset by hash.
    """

    asset = (await db.exec(select(Asset).where(Asset.hash == asset_hash))).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Not found")

    return GetAssetMetadataResponse(**asset.model_dump())


class UploadFileResponse(BaseModel):
    hash: str
    content_type: str
    alt: str | None = None


@router.post("/assets")
async def upload_asset(
    file: UploadFile,
    alt: Optional[str],
    _: Annotated[Any, Depends(authorize)],
    db: Annotated[AsyncSession, Depends(db.use)],
) -> UploadFileResponse:
    """
    Uploads an asset and returns its hash.
    """

    if file.content_type is None:
        raise HTTPException(status_code=400, detail="Content-Type header is required")

    if file.size is None or file.size > UPLOAD_LIMIT:
        raise HTTPException(status_code=400, detail="File is too large")

    data = await file.read()
    hash = hash_bytes(data)
    content_type = file.content_type

    asset = Asset(
        hash=hash,
        data=data,
        content_type=content_type,
        alt=alt if alt else None,
    )
    db.add(asset)

    return UploadFileResponse(**asset.model_dump())


async def assert_asset_hash(db: AsyncSession, hash: str):
    asset = (await db.exec(select(Asset.hash).where(Asset.hash == hash))).first()
    if asset is None:
        raise HTTPException(status_code=400, detail="Asset hash does not exist")
