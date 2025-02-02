from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from core import Kaede


class RouteRequest(Request):
    app: Kaede
