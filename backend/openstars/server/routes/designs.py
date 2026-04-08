"""Designer reference and design management endpoints (PRD 18/20 MVP)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, Header

from openstars.engine.component_catalogue import (
    CatalogueLoadError,
    ComponentCatalogueEntry,
    ComponentType,
    load_component_catalogue,
    serialise_component_entry,
)
from openstars.engine.hull_definitions import HullDefinition, HullSlotDefinition, load_hull_registry
from openstars.engine.ids import create_id
from openstars.engine.models import Design, DesignCost, Minerals, Scanner
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1/games/{game_id}", tags=["designs"])


@lru_cache
def _catalogue():
    return load_component_catalogue()


@lru_cache
def _hulls():
    return load_hull_registry()


def _validate_player(storage: GameStorage, game_id: str, username: str):
    try:
        meta = storage.load_game_meta(game_id)
    except FileNotFoundError:
        return None, error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")
    if username not in meta.get("players", []):
        return None, error_response(
            403,
            "NOT_PARTICIPANT",
            "You are not a participant in this game",
        )
    return meta, None


def _summarise_design(design: Design) -> dict:
    return {
        "id": design.id,
        "name": design.name,
        "hull": design.hull,
        "speed": design.speed,
        "cost": design.cost.model_dump(),
    }


def _serialise_hull(hull: HullDefinition) -> dict:
    return {
        "id": hull.id,
        "name": hull.name,
        "domain": hull.domain,
        "engine_required_slots": hull.engine_required_slots,
        "slots": [
            {
                "slot_number": slot.slot_number,
                "slot_categories": slot.slot_categories,
                "capacity": slot.capacity,
                "required": slot.required,
            }
            for slot in hull.slots
        ],
    }


def _slot_by_number(hull: HullDefinition) -> dict[int, HullSlotDefinition]:
    return {slot.slot_number: slot for slot in hull.slots}


def _component_type_for_entry(entry: ComponentCatalogueEntry) -> ComponentType:
    if entry.engine is not None:
        return "engine"
    if entry.scanner is not None:
        return "scanner"
    if entry.weapon is not None:
        return "weapon"
    if entry.shield is not None:
        return "shield"
    if entry.armour is not None:
        return "armour"
    return "general_purpose"


def _compute_design_derived_stats(
    hull: HullDefinition,
    assignments: list[dict],
    component_by_id: dict[str, ComponentCatalogueEntry],
) -> tuple[int, int, Scanner, DesignCost]:
    speed = 0
    cargo_capacity = 0
    scanner_normal = 0
    scanner_penetrating = 0
    resources = 0
    ironium = 0
    boranium = 0
    germanium = 0

    for assignment in assignments:
        component = component_by_id[assignment["component_id"]]
        count = assignment["component_count"]
        cost = component.cost
        resources += cost.resources * count
        ironium += cost.ironium * count
        boranium += cost.boranium * count
        germanium += cost.germanium * count
        if component.engine is not None:
            speed = max(speed, component.engine.max_warp)
        if component.scanner is not None:
            scanner_normal = max(scanner_normal, component.scanner.normal)
            scanner_penetrating = max(scanner_penetrating, component.scanner.penetrating)
        if component.general_purpose is not None:
            cargo_capacity += component.general_purpose.cargo_capacity * count

    # Minimal hull baseline costs for the MVP.
    hull_resource_cost = 10 if hull.id == "scout" else 20
    hull_ironium_cost = 2 if hull.id == "scout" else 4
    resources += hull_resource_cost
    ironium += hull_ironium_cost

    return (
        speed,
        cargo_capacity,
        Scanner(normal=scanner_normal, penetrating=scanner_penetrating),
        DesignCost(
            resources=resources,
            minerals=Minerals(
                ironium=ironium,
                boranium=boranium,
                germanium=germanium,
            ),
        ),
    )


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
    x_player: str = Header(...),
):
    _, err = _validate_player(storage, game_id, x_player)
    if err:
        return err
    if domain != "ship":
        return error_response(400, "UNSUPPORTED_DOMAIN", f"Unsupported design domain: {domain}")

    try:
        catalogue = _catalogue()
        hulls = _hulls()
    except CatalogueLoadError as exc:
        return error_response(500, "CATALOGUE_LOAD_ERROR", str(exc))

    component_entries = []
    for component_type in sorted(catalogue.by_type):
        for entry in catalogue.by_type[component_type]:
            component_entries.append(serialise_component_entry(component_type, entry))
    return {
        "domain": "ship",
        "hulls": [_serialise_hull(hull) for hull in hulls.ship_hulls],
        "components": component_entries,
    }


@router.get("/designs")
async def get_designs(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    _, err = _validate_player(storage, game_id, x_player)
    if err:
        return err
    return {
        "designs": [_summarise_design(design) for design in storage.list_designs(game_id, x_player)]
    }


@router.get("/designs/{design_id}")
async def get_design_detail(
    game_id: str,
    design_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    _, err = _validate_player(storage, game_id, x_player)
    if err:
        return err
    try:
        design = storage.load_design(game_id, x_player, design_id)
    except FileNotFoundError:
        return error_response(404, "DESIGN_NOT_FOUND", f"Design {design_id!r} not found")
    return {"design": design.model_dump()}


@router.post("/designs", status_code=201)
async def create_design(
    game_id: str,
    payload: dict,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    try:
        catalogue = _catalogue()
        hulls = _hulls()
    except CatalogueLoadError as exc:
        return error_response(500, "CATALOGUE_LOAD_ERROR", str(exc))

    name = payload.get("name")
    hull_id = payload.get("hull")
    components = payload.get("components")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 64:
        return error_response(400, "INVALID_NAME", "Design name must be 1-64 non-space characters")
    if not isinstance(hull_id, str) or hull_id not in hulls.by_id:
        return error_response(400, "UNKNOWN_HULL", f"Unknown hull {hull_id!r}")
    if not isinstance(components, list):
        return error_response(400, "INVALID_COMPONENTS", "components must be a list")

    hull = hulls.by_id[hull_id]
    slots = _slot_by_number(hull)
    assignments_by_slot: dict[int, dict] = {}
    for index, assignment in enumerate(components):
        if not isinstance(assignment, dict):
            return error_response(
                400,
                "INVALID_COMPONENT_ASSIGNMENT",
                f"components[{index}] must be an object",
            )
        slot_number = assignment.get("slot_number")
        component_id = assignment.get("component_id")
        component_count = assignment.get("component_count")
        if not isinstance(slot_number, int) or slot_number < 1 or slot_number not in slots:
            return error_response(
                400,
                "UNKNOWN_SLOT",
                f"components[{index}] references unknown slot {slot_number!r}",
            )
        if not isinstance(component_id, str) or component_id not in catalogue.by_id:
            return error_response(
                400,
                "UNKNOWN_COMPONENT",
                f"components[{index}] references unknown component {component_id!r}",
            )
        if not isinstance(component_count, int):
            return error_response(
                400,
                "INVALID_COMPONENT_COUNT",
                f"components[{index}] component_count must be an integer",
            )
        if slot_number in assignments_by_slot:
            return error_response(
                400,
                "DUPLICATE_SLOT_ASSIGNMENT",
                f"slot {slot_number!r} assigned more than once",
            )
        slot = slots[slot_number]
        component = catalogue.by_id[component_id]
        component_type = _component_type_for_entry(component)
        if component_type not in slot.slot_categories:
            return error_response(
                400,
                "SLOT_INCOMPATIBLE_COMPONENT",
                f"slot {slot_number!r} does not accept component {component_id!r}",
            )
        if not (component.component_count_min <= component_count):
            return error_response(
                400,
                "COMPONENT_COUNT_TOO_SMALL",
                "component_count for "
                f"{slot_number!r} is below minimum {component.component_count_min}",
            )
        max_allowed = component.component_count_max
        if max_allowed is not None and component_count > max_allowed:
            return error_response(
                400,
                "COMPONENT_COUNT_TOO_LARGE",
                f"component_count for {slot_number!r} exceeds component max {max_allowed}",
            )
        if component_count > slot.capacity:
            return error_response(
                400,
                "COMPONENT_COUNT_EXCEEDS_SLOT_CAPACITY",
                f"component_count for {slot_number!r} exceeds slot capacity {slot.capacity}",
            )
        assignments_by_slot[slot_number] = {
            "slot_number": slot_number,
            "component_id": component_id,
            "component_count": component_count,
        }

    required_slots = [slot.slot_number for slot in hull.slots if slot.required]
    missing_required_slots = [
        slot_number for slot_number in required_slots if slot_number not in assignments_by_slot
    ]
    if missing_required_slots:
        return error_response(
            400,
            "REQUIRED_SLOT_MISSING",
            "Required slots are missing assignments: "
            f"{', '.join(str(slot_number) for slot_number in sorted(missing_required_slots))}",
        )

    speed, cargo_capacity, scanner, cost = _compute_design_derived_stats(
        hull=hull,
        assignments=[assignments_by_slot[key] for key in sorted(assignments_by_slot)],
        component_by_id=catalogue.by_id,
    )
    if speed <= 0:
        return error_response(
            400,
            "MISSING_ENGINE",
            "Design must include at least one engine assignment",
        )

    game_seed = int(meta.get("seed", hash(game_id) & 0xFFFFFFFF))
    design_id = _next_design_id(storage, game_id, x_player, game_seed)
    design = Design(
        id=design_id,
        owner=x_player,
        name=name.strip(),
        hull=hull.id,
        speed=speed,
        scanner=scanner,
        cargo_capacity=cargo_capacity,
        cost=cost,
    )
    storage.save_design(game_id, x_player, design)
    return {"design": design.model_dump()}
