"""Hull definitions used by the first-pass ship designer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DesignDomain = Literal["ship", "starbase"]
SlotCategory = Literal["engine", "scanner", "weapon", "shield", "armour", "general_purpose"]
SLOT_CATEGORIES: tuple[SlotCategory, ...] = (
    "engine",
    "scanner",
    "weapon",
    "shield",
    "armour",
    "general_purpose",
)


class HullSlotDefinition(BaseModel):
    slot_id: str
    slot_categories: list[SlotCategory] = Field(min_length=1)
    capacity: int = Field(ge=1)
    required: bool = False


class HullDefinition(BaseModel):
    id: str
    name: str
    domain: DesignDomain
    engine_required_slots: int = Field(ge=0)
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
            slots=[
                HullSlotDefinition(
                    slot_id="engine_1",
                    slot_categories=["engine"],
                    capacity=1,
                    required=True,
                ),
                HullSlotDefinition(
                    slot_id="scanner_1",
                    slot_categories=["scanner"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_id="general_1",
                    slot_categories=["general_purpose"],
                    capacity=1,
                ),
            ],
        ),
        HullDefinition(
            id="destroyer",
            name="Destroyer",
            domain="ship",
            engine_required_slots=1,
            slots=[
                HullSlotDefinition(
                    slot_id="engine_1",
                    slot_categories=["engine"],
                    capacity=1,
                    required=True,
                ),
                HullSlotDefinition(
                    slot_id="weapon_1",
                    slot_categories=["weapon"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_id="weapon_2",
                    slot_categories=["weapon"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_id="general_1",
                    slot_categories=["general_purpose"],
                    capacity=1,
                ),
                HullSlotDefinition(
                    slot_id="armour_1",
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
        slot_ids = [slot.slot_id for slot in hull.slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError(f"hull {hull.id!r} defines duplicate slot_id values")
        by_id[hull.id] = hull
    return HullRegistry(ship_hulls=hulls, by_id=by_id)
