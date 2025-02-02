from typing import AsyncGenerator

import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.exc
import sqlalchemy.ext.asyncio
import sqlalchemy.ext.asyncio.session
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from .request import RouteRequest


# For async info on SQLModel, see
# https://github.com/tiangolo/sqlmodel/pull/58.
async def use(request: RouteRequest) -> AsyncGenerator[AsyncSession, None]:
    """
    This function is a context manager that yields a database session.
    Use this in FastAPI route functions to access the database.
    """
    async with request.app.get() as session:
        try:
            yield session
            await session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=409, detail="Conflict")
        except:
            await session.rollback()
            raise
