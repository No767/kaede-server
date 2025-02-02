from core import Kaede
from fastapi import Request


class RouteRequest(Request):
    app: Kaede
