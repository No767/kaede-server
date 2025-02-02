from __future__ import annotations

from typing import Annotated, Any, Generic, Optional, Sequence, TypeVar

from fastapi import Query
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from fastapi_pagination.types import GreaterEqualOne, GreaterEqualZero

T = TypeVar("T")


class KaedeParams(AbstractParams):
    page: Annotated[int, Query(default=1, ge=1)]
    size: Annotated[int, Query(default=50, ge=1, le=100)]

    def __init__(self, page: int = 1, size: int = 50):
        self.page = page
        self.size = size

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=(self.page - 1) * self.size,
            include_total=True,  # skip total calculation
        )


class KaedeOffsetParams(AbstractParams):
    limit: int = Query(50, ge=1, le=100, description="Page size limit")
    offset: int = Query(0, ge=0, description="Page offset")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.limit,
            offset=self.offset,
        )


class KaedeOffsetPage(AbstractPage[T], Generic[T]):
    limit: Optional[GreaterEqualOne]
    offset: Optional[GreaterEqualZero]

    __params_type__ = KaedeOffsetParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: KaedeOffsetParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> KaedeOffsetPage[T]:
        raw_params = params.to_raw_params().as_limit_offset()

        return cls(
            cls,
            total=total,
            items=items,
            limit=raw_params.limit,
            offset=raw_params.offset,
            **kwargs,
        )


class KaedePages(AbstractPage[T], Generic[T]):
    data: list[T]
    total: int

    __params_type__ = KaedeParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: KaedeParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> KaedePages[T]:
        assert total is not None, "total must be provided"

        return cls(
            data=items,
            total=total,
        )
