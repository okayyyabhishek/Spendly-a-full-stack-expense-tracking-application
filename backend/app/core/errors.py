"""Consistent public error response helpers."""

from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    """Avoid leaking database or stack details through the API."""
    return error_response(500, "internal_server_error", "Something went wrong. Please try again.")
