from typing import TYPE_CHECKING, AsyncGenerator

import sqlalchemy
from fastapi import HTTPException

if TYPE_CHECKING:
    from .requests import RouteRequest
    from .types import Database


# For async info on SQLModel, see
# https://github.com/tiangolo/sqlmodel/pull/58.
async def use(request: RouteRequest) -> AsyncGenerator[Database, None]:
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
