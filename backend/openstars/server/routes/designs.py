"""Designer reference and design management endpoints (PRD 18/20 MVP)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends

from openstars.engine.component_catalogue import (
    CatalogueLoadError,
    ComponentCatalogueEntry,
    DesignDomain,
    load_component_catalogue,
)
from openstars.engine.designs import (
    DesignValidationError,
    build_design,
    is_entry_available_for_player,
)
from openstars.engine.ids import create_id
from openstars.engine.models import Design, Player
from openstars.game_directory.base import GameSummary
from openstars.server.auth import GamePlayer, get_game_player
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1/games/{game_id}", tags=["designs"])


@lru_cache
def _catalogue():
    return load_component_catalogue()


def _summarise_design(design: Design) -> dict:
    return {
        "id": design.id,
        "name": design.name,
        "hull": design.hull,
        "fuel_capacity": design.fuel_capacity,
        "cost": design.cost.model_dump(),
    }


def _hulls_for_domain(
    catalogue: object,
    domain: DesignDomain,
) -> list[ComponentCatalogueEntry]:
    return [
        entry
        for entry in catalogue.by_type["hull"]
        if entry.hull is not None and entry.hull.domain == domain and entry.hull.slots
    ]


def _player_for_game(storage: GameStorage, summary: GameSummary, username: str) -> Player | None:
    """Find the engine player record, reusing the summary the dependency already read."""
    global_state = storage.load_global_state(summary.game_id, summary.current_turn)
    return next((player for player in global_state.players if player.username == username), None)


def _next_design_id(storage: GameStorage, game_id: str, username: str, game_seed: int) -> str:
    existing_ids = {design.id for design in storage.list_designs(game_id, username)}
    counter = len(existing_ids) + 10_000
    while True:
        candidate = create_id(counter, game_seed, "DE")
        if candidate not in existing_ids:
            return candidate
        counter += 1


@router.get("/designs/reference-data")
async def get_design_reference_data(
    game_id: str,
    domain: str = "ship",
    storage: GameStorage = Depends(get_storage),
    context: GamePlayer = Depends(get_game_player),
):
    summary, player_name = context
    if domain not in {"ship", "starbase"}:
        return error_response(400, "UNSUPPORTED_DOMAIN", f"Unsupported design domain: {domain}")

    try:
        catalogue = _catalogue()
    except CatalogueLoadError as exc:
        return error_response(500, "CATALOGUE_LOAD_ERROR", str(exc))

    player = _player_for_game(storage, summary, player_name)
    if player is None:
        return error_response(403, "NOT_PARTICIPANT", "You are not a participant in this game")

    component_entries = []
    for component_type in sorted(catalogue.by_type):
        for entry in catalogue.by_type[component_type]:
            if is_entry_available_for_player(entry, player.research_state.levels, player.race):
                component_entries.append(entry.model_dump(exclude_none=True))
    return {
        "domain": domain,
        "hulls": [
            hull.model_dump(exclude_none=True)
            for hull in _hulls_for_domain(catalogue, domain)
            if is_entry_available_for_player(hull, player.research_state.levels, player.race)
        ],
        "components": component_entries,
    }


@router.get("/designs")
async def get_designs(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    context: GamePlayer = Depends(get_game_player),
):
    return {
        "designs": [
            _summarise_design(design) for design in storage.list_designs(game_id, context.player)
        ]
    }


@router.get("/designs/{design_id}")
async def get_design_detail(
    game_id: str,
    design_id: str,
    storage: GameStorage = Depends(get_storage),
    context: GamePlayer = Depends(get_game_player),
):
    try:
        design = storage.load_design(game_id, context.player, design_id)
    except FileNotFoundError:
        return error_response(404, "DESIGN_NOT_FOUND", f"Design {design_id!r} not found")
    return {"design": design.model_dump()}


@router.post("/designs", status_code=201)
async def create_design(
    game_id: str,
    payload: dict,
    storage: GameStorage = Depends(get_storage),
    context: GamePlayer = Depends(get_game_player),
):
    summary, player_name = context

    try:
        catalogue = _catalogue()
    except CatalogueLoadError as exc:
        return error_response(500, "CATALOGUE_LOAD_ERROR", str(exc))

    game_seed = summary.seed
    design_id = _next_design_id(storage, game_id, player_name, game_seed)
    player = _player_for_game(storage, summary, player_name)
    if player is None:
        return error_response(403, "NOT_PARTICIPANT", "You are not a participant in this game")

    try:
        design = build_design(
            design_id=design_id,
            owner=player_name,
            name=payload.get("name"),
            hull_id=payload.get("hull"),
            components=payload.get("components"),
            catalogue=catalogue,
            player_levels=player.research_state.levels,
            race=player.race,
        )
    except DesignValidationError as exc:
        return error_response(400, exc.code, exc.message)

    storage.save_design(game_id, player_name, design)
    return {"design": design.model_dump()}
