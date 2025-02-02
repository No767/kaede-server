from typing import TYPE_CHECKING, AsyncGenerator

import sqlalchemy
from fastapi import HTTPException
from utils.requests import RouteRequest

from . import models as models

if TYPE_CHECKING:
    from utils.types import Database


@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def set_sqlite_pragma(conn, _):
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=wal2")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
