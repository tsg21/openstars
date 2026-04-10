"""Hull definitions used by the first-pass ship designer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DesignDomain = Literal["ship", "starbase"]
SlotCategory = Literal["engine", "scanner", "weapon", "shield", "armour"]
SLOT_CATEGORIES: tuple[SlotCategory, ...] = (
    "engine",
    "scanner",
    "weapon",
    "shield",
    "armour",
)

HULL_MASS_BY_ID: dict[str, int] = {
    "scout": 8,
    "destroyer": 30,
    "small_freighter": 25,
    "colony_ship": 20,
}


class HullSlotDefinition(BaseModel):
    slot_number: int = Field(ge=1)
    slot_categories: list[SlotCategory] = Field(min_length=1)
    capacity: int = Field(ge=1)
    required: bool = False


class HullDefinition(BaseModel):
    id: str
    name: str
    domain: DesignDomain
    engine_required_slots: int = Field(ge=0)
    fuel_capacity: int = Field(ge=0, default=0)
    slots: list[HullSlotDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_engine_required_slots(self) -> HullDefinition:
        engine_slots = [slot for slot in self.slots if "engine" in slot.slot_categories]
        if len(engine_slots) < self.engine_required_slots:
            raise ValueError("engine_required_slots exceeds available engine slots")
        return self


@dataclass(frozen=True)
class HullRegistry:
    ship_hulls: list[HullDefinition]
    by_id: dict[str, HullDefinition]


def ship_hull_definitions() -> list[HullDefinition]:
    """Return MVP hull definitions for ship design domain."""
    return [
        HullDefinition(
            id="scout",
            name="Scout",
            domain="ship",
            engine_required_slots=1,
            fuel_capacity=50,
            slots=[
                HullSlotDefinition(
                    slot_number=1,
                    slot_categories=["engine"],
                    capacity=1,
                    required=True,
                ),
                HullSlotDefinition(
                    slot_number=2,
                    slot_categories=["scanner"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_number=3,
                    slot_categories=["armour"],
                    capacity=1,
                ),
            ],
        ),
        HullDefinition(
            id="destroyer",
            name="Destroyer",
            domain="ship",
            engine_required_slots=1,
            fuel_capacity=120,
            slots=[
                HullSlotDefinition(
                    slot_number=1,
                    slot_categories=["engine"],
                    capacity=1,
                    required=True,
                ),
                HullSlotDefinition(
                    slot_number=2,
                    slot_categories=["weapon"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_number=3,
                    slot_categories=["weapon"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_number=4,
                    slot_categories=["shield"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_number=5,
                    slot_categories=["armour"],
                    capacity=2,
                ),
            ],
        ),
    ]


def load_hull_registry() -> HullRegistry:
    hulls = ship_hull_definitions()
    by_id = {}
    for hull in hulls:
        if hull.id in by_id:
            raise ValueError(f"duplicate hull id {hull.id!r}")
        slot_numbers = [slot.slot_number for slot in hull.slots]
        if len(slot_numbers) != len(set(slot_numbers)):
            raise ValueError(f"hull {hull.id!r} defines duplicate slot_number values")
        by_id[hull.id] = hull
    return HullRegistry(ship_hulls=hulls, by_id=by_id)


def hull_mass_for_id(hull_id: str) -> int:
    return HULL_MASS_BY_ID.get(hull_id, 0)
