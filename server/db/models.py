import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel
from sqlmodel import (
    JSON,
    Column,
    Field,
    SQLModel,
)

from .id import generate_id


class RoleAccess(int, Enum):
    PUBLIC = 0
    MOD = 1
    ADMIN = 2
    HIGHEST = ADMIN


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    expires_at: datetime = Field(default=datetime.now(timezone.utc))


class Asset(SQLModel, table=True):
    """
    An asset is any arbitrary binary data that can be stored in the database.
    It is identified by the base64-encoded SHA-256 hash of the data.
    Content types are supplied by the server.
    """

    hash: str = Field(primary_key=True)
    data: bytes
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    content_type: str
    alt: str | None = Field(default=None)


# We need to put some validation
class Book(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(index=True)
    description: str
    image_hash: Optional[str] = Field(default=None, foreign_key="asset.hash")
    author: int = Field(default=None, foreign_key="author.id")
    owner: int = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))


class User(SQLModel, table=True):
    id: int = Field(default_factory=generate_id, primary_key=True)
    name: str
    email: str
    bio: str
    avatar_hash: Optional[str] = Field(default=None, foreign_key="asset.hash")
    created_at: datetime = Field(default=datetime.now(timezone.utc))


class Tags(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    description: str


class Author(SQLModel, table=True):
    id: int = Field(default_factory=generate_id, primary_key=True)
    name: str
    bio: str
    avatar_hash: Optional[str] = Field(
        default=None, foreign_key="asset.hash", primary_key=True
    )
    created_at: datetime = Field(default=datetime.now(timezone.utc))


class CommentContentText(BaseModel):
    """
    A message that contains Markdown text.
    """

    type: Literal["text"]
    markdown: str


class CommentContentSticker(BaseModel):
    """
    A message that contains a single sticker.
    """

    type: Literal["sticker"]
    asset_hash: str


class CommentContentImage(BaseModel):
    """
    A message that contains a single image.
    """

    type: Literal["image"]
    asset_hash: str


CommentContent = Annotated[
    Union[CommentContentText, CommentContentSticker, CommentContentImage],
    Field(default={}, discriminator="type", sa_column=Column(JSON)),
]


class CommentMessage(SQLModel, table=True):
    # id is the unique identifier for the message.
    # It is defined as a Snowflake ID and therefore also contains a timestamp.
    id: int = Field(default_factory=generate_id, primary_key=True)

    book_id: int | None = Field(foreign_key="book.id")

    author_id: int | None = Field(foreign_key="user.id")

    content: CommentContent | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default=datetime.now(timezone.utc))


class UserPhoto(SQLModel, table=True):
    user_id: Optional[int] = Field(foreign_key="user.id", primary_key=True)
    photo_hash: Optional[str] = Field(
        default=None, foreign_key="asset.hash", primary_key=True
    )


class UserPassword(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, foreign_key="user.id")
    passhash: str


# Many-to-Many tables


class UserCollection(SQLModel, table=True):
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    book_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="book.id", primary_key=True
    )


class BookTags(SQLModel, table=True):
    tag_id: Optional[int] = Field(default=None, foreign_key="tags.id", primary_key=True)
    book_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="book.id", primary_key=True
    )
