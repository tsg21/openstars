"""Standardised error responses (PRD 09)."""

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Create a consistent error response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


class GameError(HTTPException):
    """Game-specific HTTP error with structured error body."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.error_code = code
        self.error_message = message
        super().__init__(status_code=status_code, detail=message)
