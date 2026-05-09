"""OpenStars! backend — FastAPI application."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openstars.engine.resolve_steps.commands import register_builtin_command_parsers
from openstars.server.errors import GameError
from openstars.server.logging import setup_logging

logger = logging.getLogger(__name__)
from openstars.server.routers.combat_altair_prototype import (
    router as combat_altair_router,
)
from openstars.server.routes.designs import router as designs_router
from openstars.server.routes.games import router as games_router
from openstars.server.routes.play import router as play_router
from openstars.server.routes.race import router as race_router

setup_logging()
register_builtin_command_parsers()

app = FastAPI(title="OpenStars!", version="0.1.0")

app.include_router(games_router)
app.include_router(play_router)
app.include_router(combat_altair_router)
app.include_router(designs_router)
app.include_router(race_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An internal server error occurred"}},
    )


@app.exception_handler(GameError)
async def game_error_handler(request: Request, exc: GameError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.error_message}},
    )


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
