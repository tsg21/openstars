"""OpenStars! backend — FastAPI application."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openstars.server.errors import GameError
from openstars.server.routes.games import router as games_router
from openstars.server.routes.play import router as play_router


# ---------------------------------------------------------------------------
# Suppress noisy health-check access logs
# ---------------------------------------------------------------------------
class _HealthCheckFilter(logging.Filter):
    """Drop uvicorn access-log entries for the health endpoint."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return "/api/v1/health" not in msg


logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())

app = FastAPI(title="OpenStars!", version="0.1.0")

app.include_router(games_router)
app.include_router(play_router)


@app.exception_handler(GameError)
async def game_error_handler(request: Request, exc: GameError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.error_message}},
    )


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
