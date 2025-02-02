from typing import Annotated, Optional

import db
from db.id import generate_id
from db.models import (
    Book,
    Session,
    User,
    UserCollection,
    UserPassword,
    UserPhoto,
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlmodel import (
    Field,
    select,
)
from utils.pages import KaedePages, KaedeParams
from utils.sessions import authorize, hash_password, new_session, verify_password
from utils.types import Database

from .assets import assert_asset_hash

router = APIRouter(tags=["me"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(req: LoginRequest, db: Annotated[Database, Depends(db.use)]) -> Session:
    """
    This function logs in a user and returns a session token.
    """
    user = (await db.exec(select(User).where(User.email == req.email))).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    passhash = (
        await db.exec(select(UserPassword.passhash).where(UserPassword.id == user.id))
    ).one()
    if not verify_password(req.password, passhash):
        raise HTTPException(status_code=401, detail="Unauthorized")

    assert user.id is not None
    return new_session(db, user.id)


class RegisterRequest(BaseModel):
    """
    This class is used to register a new user.
    """

    bio: str
    email: str
    password: str


@router.post("/register")
async def register(
    req: RegisterRequest, db: Annotated[Database, Depends(db.use)]
) -> Session:
    """
    This function registers a new user and returns a session token.
    """

    async with db.begin_nested():
        user = User(**req.model_dump())
        db.add(user)

    await db.refresh(user)
    assert user.id is not None

    async with db.begin_nested():
        userpw = UserPassword(id=user.id, passhash=hash_password(req.password))
        db.add(userpw)

    return new_session(db, user.id)


class MeResponse(BaseModel):
    id: int = Field(default_factory=generate_id, primary_key=True)
    name: str
    email: str
    bio: str
    avatar_hash: Optional[str]


@router.get("/users/me")
async def get_self(
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
) -> MeResponse:
    """
    This function returns the currently authenticated user.
    """
    user = (await db.exec(select(User).where(User.id == me_id))).one()

    return MeResponse(**user.model_dump())


class UpdateUserRequest(RegisterRequest):
    avatar_hash: Optional[str] = None
    photo_hashes: list[str] = []


@router.patch("/users/me")
async def update_user(
    req: UpdateUserRequest,
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
) -> User:
    """
    Updates the specified authenticated user
    """

    if req.avatar_hash is not None:
        await assert_asset_hash(db, req.avatar_hash)

    user = (await db.exec(select(User).where(User.id == me_id))).one()
    password = (
        await db.exec(select(UserPassword).where(UserPassword.id == me_id))
    ).one()

    for key, value in req.model_dump().items():
        match key:
            case "password":
                password.passhash = hash_password(value)
            case "avatar_hash":
                if value is not None:
                    await assert_asset_hash(db, value)
                setattr(user, key, value)
            case "photo_hashes":
                pass  # handled later
            case _:
                setattr(user, key, value)

    new_photos = req.photo_hashes.copy()
    old_photos = (
        await db.exec(select(UserPhoto).where(UserPhoto.user_id == me_id))
    ).all()

    for photo in old_photos:
        if photo.photo_hash not in req.photo_hashes:
            # Old photo is not in new photos, delete it.
            await db.delete(photo)
        else:
            # Old photo is in new photos, remove it from new photos.
            new_photos.remove(photo.photo_hash)

    # Add the new photos.
    for photo in new_photos:
        db.add(UserPhoto(user_id=me_id, photo_hash=photo))

    db.add(user)
    db.add(password)

    await db.commit()
    await db.refresh(user)

    return user


@router.get("/users/me/books")
async def get_my_books(
    me_id: Annotated[int, Depends(authorize)],
    db: Annotated[Database, Depends(db.use)],
    *,
    params: Annotated[KaedeParams, Depends()],
) -> KaedePages[Book]:
    """Get the authenticated user's collection of books"""
    query = (
        select(User)
        .join(UserCollection)
        .join(Book)
        .where(UserCollection.user_id == me_id)
        .where(Book.id == UserCollection.book_id)
    )
    return await paginate(db, query, params)
