"""OpenStars! backend — FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openstars.server.errors import GameError
from openstars.server.logging import setup_logging
from openstars.server.routers.combat_altair_prototype import (
    router as combat_altair_router,
)
from openstars.server.routes.designs import router as designs_router
from openstars.server.routes.games import router as games_router
from openstars.server.routes.play import router as play_router

setup_logging()

app = FastAPI(title="OpenStars!", version="0.1.0")

app.include_router(games_router)
app.include_router(play_router)
app.include_router(combat_altair_router)
app.include_router(designs_router)


@app.exception_handler(GameError)
async def game_error_handler(request: Request, exc: GameError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.error_message}},
    )


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
