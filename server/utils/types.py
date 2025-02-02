from typing import TypeAlias

from sqlmodel.ext.asyncio.session import AsyncSession

Database: TypeAlias = AsyncSession
