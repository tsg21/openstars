"""Component catalogue models and YAML loader for designer APIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

ComponentType = Literal[
    "engine",
    "scanner",
    "weapon",
    "torpedo",
    "shield",
    "armour",
    "electrical",
    "mechanical",
    "planetary",
    "hull",
]
DesignDomain = Literal["ship", "starbase"]
SlotCategory = Literal[
    "engine",
    "scanner",
    "weapon",
    "shield",
    "armour",
    "general_purpose",
    "electrical",
    "mechanical",
    "bomb",
    "mine_layer",
    "robot_miner",
    "orbital",
]

COMPONENT_CATALOGUE_PATHS: tuple[Path, ...] = (
    Path("components/engines.yaml"),
    Path("components/scanners.yaml"),
    Path("components/weapons.yaml"),
    Path("components/torpedoes.yaml"),
    Path("components/shields.yaml"),
    Path("components/armour.yaml"),
    Path("components/electrical.yaml"),
    Path("components/mechanical.yaml"),
    Path("components/planetary.yaml"),
    Path("hulls.yaml"),
)


class CatalogueLoadError(RuntimeError):
    """Raised when component catalogue files fail to parse or validate."""


class ComponentCost(BaseModel):
    resources: int = Field(default=0, ge=0)
    ironium: int = Field(default=0, ge=0)
    boranium: int = Field(default=0, ge=0)
    germanium: int = Field(default=0, ge=0)


class EngineStats(BaseModel):
    fuel_usage: list[int]
    is_ramscoop: bool = False

    @model_validator(mode="after")
    def validate_fuel_usage(self) -> EngineStats:
        if len(self.fuel_usage) != 10:
            raise ValueError("fuel_usage must contain exactly 10 entries (warp 1..10)")
        if any(value < 0 for value in self.fuel_usage):
            raise ValueError("fuel_usage values must be >= 0")
        return self


class ScannerStats(BaseModel):
    normal: int = Field(ge=0)
    penetrating: int = Field(ge=0)


class WeaponStats(BaseModel):
    range: int = Field(ge=0)
    damage: int = Field(ge=0)
    initiative: int = Field(ge=0)


class TorpedoStats(BaseModel):
    range: int = Field(ge=0)
    damage: int = Field(ge=0)
    initiative: int = Field(ge=0)
    hit_chance: int = Field(ge=0, le=100)


class ShieldStats(BaseModel):
    shield_points: int = Field(ge=0)


class ArmourStats(BaseModel):
    armour_points: int = Field(ge=0)


class ElectricalStats(BaseModel):
    ability: int


class MechanicalStats(BaseModel):
    ability: int


class PlanetaryStats(BaseModel):
    ability: int


class TechRequirements(BaseModel):
    model_config = {"extra": "forbid"}

    energy: int = Field(default=0, ge=0)
    weapons: int = Field(default=0, ge=0)
    propulsion: int = Field(default=0, ge=0)
    construction: int = Field(default=0, ge=0)
    electronics: int = Field(default=0, ge=0)
    biotechnology: int = Field(default=0, ge=0)


class GridPosition(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class GridSize(BaseModel):
    w: int = Field(default=1, ge=1)
    h: int = Field(default=1, ge=1)


class GridRect(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(default=1, ge=1)
    h: int = Field(default=1, ge=1)


class HullStats(BaseModel):
    domain: DesignDomain = "ship"
    fuel_capacity: int = Field(ge=0)
    cargo_capacity: int = Field(default=0, ge=0)
    dock_capacity: int = Field(default=0)
    armour_points: int = Field(ge=0)
    initiative: int = Field(ge=0)
    layout_grid: GridSize | None = None
    cargo_layout: GridRect | None = None
    dock_layout: GridRect | None = None
    slots: list[HullSlotDefinition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_slots(self) -> HullStats:
        slot_numbers = [slot.slot_number for slot in self.slots]
        if len(slot_numbers) != len(set(slot_numbers)):
            raise ValueError("slots define duplicate slot_number values")
        return self


class HullSlotDefinition(BaseModel):
    slot_number: int = Field(ge=1)
    slot_categories: list[SlotCategory] = Field(min_length=1)
    capacity: int = Field(ge=1)
    required: bool = False
    position: GridPosition | None = None
    size: GridSize = Field(default_factory=lambda: GridSize(w=2, h=2))


class ComponentCatalogueEntry(BaseModel):
    id: str
    name: str
    component_type: ComponentType
    cost: ComponentCost = Field(default_factory=ComponentCost)
    mass: int = Field(ge=0)
    tech_requirements: TechRequirements = Field(default_factory=TechRequirements)
    engine: EngineStats | None = None
    scanner: ScannerStats | None = None
    weapon: WeaponStats | None = None
    torpedo: TorpedoStats | None = None
    shield: ShieldStats | None = None
    armour: ArmourStats | None = None
    electrical: ElectricalStats | None = None
    mechanical: MechanicalStats | None = None
    planetary: PlanetaryStats | None = None
    hull: HullStats | None = None
    prt_required: list[str] = Field(default_factory=list)
    prt_forbidden: list[str] = Field(default_factory=list)
    lrt_required: list[str] = Field(default_factory=list)
    lrt_forbidden: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_stats(self) -> ComponentCatalogueEntry:
        stat_field_by_type: dict[ComponentType, str] = {
            "engine": "engine",
            "scanner": "scanner",
            "weapon": "weapon",
            "torpedo": "torpedo",
            "shield": "shield",
            "armour": "armour",
            "electrical": "electrical",
            "mechanical": "mechanical",
            "planetary": "planetary",
            "hull": "hull",
        }
        expected_field = stat_field_by_type[self.component_type]
        present_fields = [
            field_name
            for field_name in stat_field_by_type.values()
            if getattr(self, field_name) is not None
        ]
        if present_fields != [expected_field]:
            raise ValueError(
                f"must define exactly one stats block for {self.component_type!r}, "
                f"found {present_fields}"
            )
        return self


class ComponentCatalogueDocument(BaseModel):
    schema_version: int
    components: list[ComponentCatalogueEntry]


@dataclass(frozen=True)
class ComponentCatalogue:
    """Loaded component catalogue indexed by ID and type."""

    by_id: dict[str, ComponentCatalogueEntry]
    by_type: dict[ComponentType, list[ComponentCatalogueEntry]]


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def _document_path(base_dir: Path, relative_path: Path) -> Path:
    return base_dir / relative_path


def _load_one_document(path: Path) -> ComponentCatalogueDocument:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise CatalogueLoadError(f"{path.name}: failed to parse YAML ({exc})") from exc
    if not isinstance(raw, dict):
        raise CatalogueLoadError(f"{path.name}: top-level YAML document must be a mapping")
    try:
        return ComponentCatalogueDocument.model_validate(raw)
    except ValidationError as exc:
        message = _first_validation_error(exc)
        raise CatalogueLoadError(f"{path.name}: {message}") from exc


def _first_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    index_error = next(
        (
            error
            for error in errors
            if "components" in error["loc"] and isinstance(error["loc"][-1], int)
        ),
        None,
    )
    error = index_error or errors[0]
    location = ".".join(str(part) for part in error["loc"])
    return f"{location}: {error['msg']}"


def load_component_catalogue(base_dir: Path | None = None) -> ComponentCatalogue:
    """Load and validate all component YAML files."""
    components_dir = base_dir or _data_dir()
    by_id: dict[str, ComponentCatalogueEntry] = {}
    by_type: dict[ComponentType, list[ComponentCatalogueEntry]] = {
        component_type: [] for component_type in get_args(ComponentType)
    }

    for relative_path in COMPONENT_CATALOGUE_PATHS:
        path = _document_path(components_dir, relative_path)
        if not path.exists():
            raise CatalogueLoadError(f"{relative_path.name}: expected file is missing")
        document = _load_one_document(path)
        for index, component in enumerate(document.components):
            if component.id in by_id:
                raise CatalogueLoadError(
                    f"{path.name}: components[{index}] duplicate id {component.id!r}"
                )
            by_id[component.id] = component
            by_type[component.component_type].append(component)

    return ComponentCatalogue(by_id=by_id, by_type=by_type)
