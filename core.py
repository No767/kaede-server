from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Self

import orjson
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.exc
import sqlalchemy.ext.asyncio
import sqlalchemy.ext.asyncio.session
import sqlmodel
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from utils.config import KaedeConfig

__title__ = "Kaede"
__description__ = """
Project for 2025 QWER Hacks
"""
__version__ = "0.1.0a"


class Kaede(FastAPI):
    engine: sqlalchemy.ext.asyncio.AsyncEngine

    def __init__(
        self, *, loop: Optional[asyncio.AbstractEventLoop] = None, config: KaedeConfig
    ):
        self.loop: asyncio.AbstractEventLoop = (
            loop or asyncio.get_event_loop_policy().get_event_loop()
        )
        super().__init__(
            title=__title__,
            description=__description__,
            version=__version__,
            default_response_class=ORJSONResponse,
            loop=self.loop,
            redoc_url="/docs",
            docs_url=None,
            lifespan=self.lifespan,
        )
        self.config = config
        self.engine = sqlalchemy.ext.asyncio.create_async_engine(
            url=self.config["sqlite_url"],
            echo=self.config["echo"],
            json_serializer=orjson.dumps,
            json_deserializer=orjson.loads,
        )

    ### Server-related utilities

    def get(self) -> AsyncSession:
        """
        This function returns a new database session.
        """
        return AsyncSession(self.engine)

    async def init_db(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(sqlmodel.SQLModel.metadata.create_all)

    @asynccontextmanager
    async def lifespan(self, app: Self):
        await self.init_db()
        yield
