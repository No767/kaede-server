from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, AsyncGenerator

import db
from db.models import Session
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

if TYPE_CHECKING:
    from .types import Database

SESSION_EXPIRY = timedelta(days=7)
SESSION_RENEW_AFTER = timedelta(days=1)


async def authorize(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    db: Annotated[Database, Depends(db.use)],
) -> AsyncGenerator[int, None]:
    """
    This function asserts the authorization header and returns the user ID if
    the token is valid.
    """

    authorization = creds.credentials
    now = datetime.now()

    session_query = await db.exec(
        select(Session).where(
            Session.token == authorization and Session.expires_at > now
        )
    )
    session = session_query.first()
    if session is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # If the session is after the renew threshold, renew the session.
    # Don't always renew the session, as that would force a database write on
    # every request.
    if (session.expires_at - SESSION_EXPIRY) + SESSION_RENEW_AFTER < now:
        async with db.begin_nested():
            session.expires_at = datetime.now() + SESSION_EXPIRY
            db.add(session)
            await db.commit()

    assert session.user_id is not None
    yield session.user_id


def new_session(db: Database, user_id: int) -> Session:
    """
    This function creates a new session for a user and adds it to the database.
    The session is returned.
    """
    session = Session(
        token=generate_token(),
        user_id=user_id,
        expires_at=datetime.now() + SESSION_EXPIRY,
    )
    db.add(session)
    return session


def generate_token() -> str:
    """
    This function generates a random token.
    """
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    This function hashes a password.
    """
    salt = secrets.token_bytes(16)
    hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return f"{salt.hex()}${hash.hex()}"


def verify_password(password: str, shash: str) -> bool:
    """
    This function verifies a password.
    """
    ssalt, shash = shash.split("$")
    osalt = bytes.fromhex(ssalt)
    ohash = bytes.fromhex(shash)
    return hmac.compare_digest(
        ohash,
        hashlib.pbkdf2_hmac("sha256", password.encode(), osalt, 100000),
    )
