"""Pure helpers for per-planet production resolution."""

import logging
from dataclasses import dataclass
from typing import Literal

from openstars.engine.models import (
    Fleet,
    FleetComposition,
    GameEvent,
    Minerals,
    PlanetStarbaseState,
    PlanetState,
    Position,
    ProductionProgress,
    ProductionQueueItem,
    StarbaseType,
)
from openstars.engine.turn_context import TurnContext

log = logging.getLogger(__name__)

ProductionItemType = Literal["mine", "factory", "starbase", "ship"]


@dataclass(frozen=True)
class ProductionCost:
    resources: int
    minerals: Minerals


PRODUCTION_COSTS: dict[ProductionItemType, ProductionCost] = {
    "mine": ProductionCost(resources=5, minerals=Minerals()),
    "factory": ProductionCost(resources=10, minerals=Minerals(germanium=4)),
    "starbase": ProductionCost(resources=0, minerals=Minerals()),
}

STARBASE_TOTAL_COSTS: dict[StarbaseType, ProductionCost] = {
    "orbital_fort": ProductionCost(
        resources=80,
        minerals=Minerals(ironium=40, boranium=20, germanium=10),
    ),
    "space_station": ProductionCost(
        resources=160,
        minerals=Minerals(ironium=80, boranium=40, germanium=20),
    ),
}


def get_production_cost(item_type: ProductionItemType) -> ProductionCost:
    """Return the per-unit cost for a supported production item."""
    return PRODUCTION_COSTS[item_type]


def _starbase_can_build_ships(starbase_type: StarbaseType) -> bool:
    return starbase_type == "space_station"


def _half_credit_cost(cost: ProductionCost) -> ProductionCost:
    return ProductionCost(
        resources=cost.resources // 2,
        minerals=Minerals(
            ironium=cost.minerals.ironium // 2,
            boranium=cost.minerals.boranium // 2,
            germanium=cost.minerals.germanium // 2,
        ),
    )


def get_starbase_total_cost(starbase_type: StarbaseType) -> ProductionCost:
    return STARBASE_TOTAL_COSTS[starbase_type]


def get_starbase_build_cost(planet: PlanetState, target_type: StarbaseType) -> ProductionCost:
    target_cost = get_starbase_total_cost(target_type)
    if planet.starbase is None:
        return target_cost

    source_type = planet.starbase.type
    if source_type == target_type:
        raise ValueError(f"invalid starbase upgrade to same type {target_type}")

    source_credit = _half_credit_cost(get_starbase_total_cost(source_type))
    return ProductionCost(
        resources=max(target_cost.resources - source_credit.resources, 0),
        minerals=Minerals(
            ironium=max(target_cost.minerals.ironium - source_credit.minerals.ironium, 0),
            boranium=max(target_cost.minerals.boranium - source_credit.minerals.boranium, 0),
            germanium=max(target_cost.minerals.germanium - source_credit.minerals.germanium, 0),
        ),
    )


def get_queue_item_cost(item: ProductionQueueItem, planet: PlanetState) -> ProductionCost:
    if item.item_type == "ship":
        raise ValueError("ship cost lookup requires turn context")
    if item.item_type != "starbase":
        return get_production_cost(item.item_type)
    assert item.target_type is not None
    return get_starbase_build_cost(planet, item.target_type)


def proportional_mineral_spend(resources_spent: int, cost: ProductionCost) -> Minerals:
    """Return total mineral progress implied by current resource progress."""
    return Minerals(
        ironium=(resources_spent * cost.minerals.ironium) // cost.resources,
        boranium=(resources_spent * cost.minerals.boranium) // cost.resources,
        germanium=(resources_spent * cost.minerals.germanium) // cost.resources,
    )


def largest_payable_resource_increment(
    progress: ProductionProgress,
    available_resources: int,
    available_minerals: Minerals,
    cost: ProductionCost,
) -> int:
    """Return the largest deterministic resource increment payable right now."""
    remaining_resources = cost.resources - progress.resources_spent
    resource_increment = min(available_resources, remaining_resources)

    while resource_increment > 0:
        post_increment = progress.resources_spent + resource_increment
        target_spend = proportional_mineral_spend(post_increment, cost)

        if (
            target_spend.ironium - progress.minerals_spent.ironium <= available_minerals.ironium
            and target_spend.boranium - progress.minerals_spent.boranium
            <= available_minerals.boranium
            and target_spend.germanium - progress.minerals_spent.germanium
            <= available_minerals.germanium
        ):
            return resource_increment

        resource_increment -= 1

    return 0


def spend_production_increment(
    progress: ProductionProgress,
    available_resources: int,
    available_minerals: Minerals,
    cost: ProductionCost,
) -> tuple[ProductionProgress, int, Minerals]:
    """Apply the largest payable increment to progress and return remaining pools."""
    resource_increment = largest_payable_resource_increment(
        progress=progress,
        available_resources=available_resources,
        available_minerals=available_minerals,
        cost=cost,
    )
    if resource_increment == 0:
        return progress.model_copy(deep=True), available_resources, available_minerals.model_copy()

    resources_spent = progress.resources_spent + resource_increment
    minerals_spent = proportional_mineral_spend(resources_spent, cost)

    return (
        ProductionProgress(
            resources_spent=resources_spent,
            minerals_spent=minerals_spent,
        ),
        available_resources - resource_increment,
        Minerals(
            ironium=available_minerals.ironium
            - (minerals_spent.ironium - progress.minerals_spent.ironium),
            boranium=available_minerals.boranium
            - (minerals_spent.boranium - progress.minerals_spent.boranium),
            germanium=available_minerals.germanium
            - (minerals_spent.germanium - progress.minerals_spent.germanium),
        ),
    )


def is_progress_complete(progress: ProductionProgress, cost: ProductionCost) -> bool:
    """Return True when a unit has been fully paid."""
    return progress.resources_spent >= cost.resources


def apply_completed_unit(planet: PlanetState, item_type: ProductionItemType) -> PlanetState:
    """Return a new planet with the completed unit effect applied."""
    if item_type == "mine":
        return planet.model_copy(update={"mines": planet.mines + 1})
    if item_type == "factory":
        return planet.model_copy(update={"factories": planet.factories + 1})
    if item_type == "ship":
        return planet
    raise ValueError("starbase completion requires target_type")


def get_ship_queue_item_cost(item: ProductionQueueItem, ctx: TurnContext) -> ProductionCost:
    if item.design_id is None:
        raise ValueError("ship production item missing design_id")
    ship_design = next((d for d in ctx.global_state.ship_designs if d.id == item.design_id), None)
    if ship_design is None:
        raise ValueError(f"unknown ship design {item.design_id}")
    return ProductionCost(resources=ship_design.cost.resources, minerals=ship_design.cost.minerals)


def _planet_coordinates(ctx: TurnContext, planet_id: str) -> tuple[int, int] | None:
    for galaxy_planet in ctx.galaxy.planets:
        if galaxy_planet.id == planet_id:
            return (galaxy_planet.x, galaxy_planet.y)
    return None


def _add_built_ship_to_fleet(ctx: TurnContext, planet: PlanetState, design_id: str) -> None:
    if planet.owner is None:
        return
    coordinates = _planet_coordinates(ctx, planet.id)
    if coordinates is None:
        return
    x, y = coordinates

    candidate_fleets = sorted(
        (
            fleet
            for fleet in ctx.fleets_by_id.values()
            if fleet.owner == planet.owner
            and fleet.position.x == x
            and fleet.position.y == y
            and any(comp.design_id == design_id and comp.count > 0 for comp in fleet.composition)
        ),
        key=lambda fleet: fleet.id,
    )
    if candidate_fleets:
        selected_fleet = candidate_fleets[0]
        updated_composition = list(selected_fleet.composition)
        for index, comp in enumerate(updated_composition):
            if comp.design_id == design_id:
                updated_composition[index] = comp.model_copy(update={"count": comp.count + 1})
                break
        ctx.fleets_by_id[selected_fleet.id] = selected_fleet.model_copy(
            update={"composition": updated_composition}
        )
        return

    fleet_id = ctx.allocate_id("FL")
    new_fleet = Fleet(
        id=fleet_id,
        name=f"Fleet #{fleet_id}",
        owner=planet.owner,
        position=Position(x=x, y=y),
        composition=[FleetComposition(design_id=design_id, count=1)],
        waypoints=[],
    )
    ctx.fleets_by_id[new_fleet.id] = new_fleet
    if all(existing_fleet.id != new_fleet.id for existing_fleet in ctx.fleets):
        ctx.fleets.append(new_fleet)


def apply_completed_starbase(planet: PlanetState, target_type: StarbaseType) -> PlanetState:
    return planet.model_copy(
        update={
            "starbase": PlanetStarbaseState(
                type=target_type,
                can_build_ships=_starbase_can_build_ships(target_type),
            )
        }
    )


def consume_completed_unit(item: ProductionQueueItem) -> ProductionQueueItem | None:
    """Decrement a queue item after a completed unit and reset current-unit progress."""
    if item.quantity == 1:
        return None

    return item.model_copy(
        update={
            "quantity": item.quantity - 1,
            "progress": ProductionProgress(),
        }
    )


def remove_queue_item_quantity(
    item: ProductionQueueItem,
    quantity: int,
    *,
    discard_in_progress_unit: bool,
) -> ProductionQueueItem | None:
    """Remove quantity from a queue item, optionally discarding current partial progress."""
    if quantity >= item.quantity:
        return None

    updated_item = item.model_copy(update={"quantity": item.quantity - quantity})
    if not discard_in_progress_unit:
        return updated_item

    return updated_item.model_copy(update={"progress": ProductionProgress()})


def resolve_production(ctx: TurnContext) -> None:
    """Resolve production for all owned planets.

    Mutates ctx.planets_by_id in-place. Accumulates events into ctx.owner_events.
    Events are aggregated per planet and item type for the turn.
    """
    for planet_id in sorted(ctx.planets_by_id.keys()):
        planet = ctx.planets_by_id[planet_id]
        if planet.owner is None or not planet.production_queue:
            continue

        (
            updated_planet,
            completed_counts,
            completed_ship_design_counts,
        ) = resolve_planet_production(
            planet,
            ctx.planet_resources.get(planet_id, 0),
            ctx,
        )
        ctx.planets_by_id[planet_id] = updated_planet

        for item_type, quantity in completed_counts.items():
            log.debug(
                "production: planet=%s owner=%s completed %d %s",
                planet.id,
                planet.owner,
                quantity,
                item_type,
            )
            ctx.append_event(
                GameEvent(
                    owner=planet.owner,
                    source_id=planet.id,
                    code="production.completed",
                    values=[
                        quantity,
                        item_type,
                        ctx.planet_names.get(planet.id, planet.id),
                    ],
                )
            )
            if item_type == "starbase":
                ctx.append_event(
                    GameEvent(
                        owner=planet.owner,
                        source_id=planet.id,
                        code=(
                            "starbase.constructed"
                            if planet.starbase is None
                            else "starbase.upgraded"
                        ),
                        values=[ctx.planet_names.get(planet.id, planet.id)],
                    )
                )
        for design_id, quantity in completed_ship_design_counts.items():
            if quantity <= 0:
                continue
            ship_design = next(
                (design for design in ctx.global_state.ship_designs if design.id == design_id),
                None,
            )
            if ship_design is None or planet.owner is None:
                continue
            ctx.append_event(
                GameEvent(
                    owner=planet.owner,
                    source_id=planet.id,
                    code="production.ship_built",
                    values=[ctx.planet_names.get(planet.id, planet.id), ship_design.name, quantity],
                )
            )
    ctx.fleets = [ctx.fleets_by_id[fleet_id] for fleet_id in sorted(ctx.fleets_by_id.keys())]


def resolve_planet_production(
    planet: PlanetState,
    available_resources: int,
    ctx: TurnContext | None = None,
) -> tuple[PlanetState, dict[ProductionItemType, int], dict[str, int]]:
    """Resolve one planet's queue using only that turn's available resources."""
    updated_planet = planet.model_copy(deep=True)
    completed_counts: dict[ProductionItemType, int] = {}
    completed_ship_design_counts: dict[str, int] = {}
    queue_index = 0

    while queue_index < len(updated_planet.production_queue):
        item = updated_planet.production_queue[queue_index]
        if item.item_type == "ship":
            if ctx is None:
                raise ValueError("ship production resolution requires turn context")
            cost = get_ship_queue_item_cost(item, ctx)
        else:
            cost = get_queue_item_cost(item, updated_planet)

        while True:
            (
                new_progress,
                new_available_resources,
                new_available_minerals,
            ) = spend_production_increment(
                progress=item.progress,
                available_resources=available_resources,
                available_minerals=updated_planet.minerals,
                cost=cost,
            )

            if new_progress == item.progress:
                return updated_planet, completed_counts, completed_ship_design_counts

            available_resources = new_available_resources
            updated_planet = updated_planet.model_copy(
                update={
                    "minerals": new_available_minerals,
                }
            )
            item = item.model_copy(update={"progress": new_progress})

            if not is_progress_complete(item.progress, cost):
                updated_planet.production_queue[queue_index] = item
                return updated_planet, completed_counts, completed_ship_design_counts

            if item.item_type == "starbase":
                assert item.target_type is not None
                updated_planet = apply_completed_starbase(updated_planet, item.target_type)
            elif item.item_type == "ship":
                assert item.design_id is not None
                _add_built_ship_to_fleet(ctx, updated_planet, item.design_id)
                completed_ship_design_counts[item.design_id] = (
                    completed_ship_design_counts.get(item.design_id, 0) + 1
                )
            else:
                updated_planet = apply_completed_unit(updated_planet, item.item_type)
            completed_counts[item.item_type] = completed_counts.get(item.item_type, 0) + 1
            next_item = consume_completed_unit(item)
            if next_item is None:
                updated_planet.production_queue.pop(queue_index)
                break

            item = next_item
            updated_planet.production_queue[queue_index] = item

            if available_resources == 0:
                return updated_planet, completed_counts, completed_ship_design_counts

    return updated_planet, completed_counts, completed_ship_design_counts
