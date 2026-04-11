"""Component catalogue models and YAML loader for designer APIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

ComponentType = Literal["engine", "scanner", "weapon", "shield", "armour", "hull"]

COMPONENT_TYPE_FILENAMES: dict[ComponentType, str] = {
    "engine": "engines.yaml",
    "scanner": "scanners.yaml",
    "weapon": "weapons.yaml",
    "shield": "shields.yaml",
    "armour": "armour.yaml",
    "hull": "hulls.yaml",
}


class CatalogueLoadError(RuntimeError):
    """Raised when component catalogue files fail to parse or validate."""


class ComponentCost(BaseModel):
    resources: int = Field(ge=0)
    ironium: int = Field(ge=0)
    boranium: int = Field(ge=0)
    germanium: int = Field(ge=0)


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
    range: int = Field(ge=1)
    damage: int = Field(ge=0)
    initiative: int = Field(ge=0)


class ShieldStats(BaseModel):
    shield_points: int = Field(ge=0)


class ArmourStats(BaseModel):
    armour_points: int = Field(ge=0)


class TechRequirements(BaseModel):
    energy: int = Field(default=0, ge=0)
    weapons: int = Field(default=0, ge=0)
    propulsion: int = Field(default=0, ge=0)
    construction: int = Field(default=0, ge=0)
    electronics: int = Field(default=0, ge=0)
    bio_tech: int = Field(default=0, ge=0)


class HullStats(BaseModel):
    fuel_capacity: int = Field(ge=0)
    cargo_capacity: int = Field(default=0, ge=0)
    armour_points: int = Field(ge=0)
    initiative: int = Field(ge=0)


class ComponentCatalogueEntry(BaseModel):
    id: str
    name: str
    component_type: ComponentType
    cost: ComponentCost
    mass: int = Field(ge=0)
    tech_requirements: TechRequirements = Field(default_factory=TechRequirements)
    engine: EngineStats | None = None
    scanner: ScannerStats | None = None
    weapon: WeaponStats | None = None
    shield: ShieldStats | None = None
    armour: ArmourStats | None = None
    hull: HullStats | None = None

    @model_validator(mode="after")
    def validate_stats(self) -> ComponentCatalogueEntry:
        stat_field_by_type: dict[ComponentType, str] = {
            "engine": "engine",
            "scanner": "scanner",
            "weapon": "weapon",
            "shield": "shield",
            "armour": "armour",
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


def _document_path(base_dir: Path, component_type: ComponentType) -> Path:
    filename = COMPONENT_TYPE_FILENAMES[component_type]
    if component_type == "hull":
        candidates = [base_dir / filename]
        if base_dir.name == "components":
            candidates.append(base_dir.parent / filename)
    else:
        candidates = [base_dir / filename, base_dir / "components" / filename]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


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
        component_type: [] for component_type in COMPONENT_TYPE_FILENAMES
    }

    for component_type in sorted(COMPONENT_TYPE_FILENAMES):
        filename = COMPONENT_TYPE_FILENAMES[component_type]
        path = _document_path(components_dir, component_type)
        if not path.exists():
            raise CatalogueLoadError(f"{filename}: expected file is missing")
        document = _load_one_document(path)
        for index, component in enumerate(document.components):
            if component.component_type != component_type:
                raise CatalogueLoadError(
                    f"{filename}: components[{index}].component_type "
                    f"{component.component_type!r} does not match file type "
                    f"{component_type!r}"
                )
            if component.id in by_id:
                raise CatalogueLoadError(
                    f"{filename}: components[{index}] duplicate id {component.id!r}"
                )
            by_id[component.id] = component
            by_type[component_type].append(component)

    return ComponentCatalogue(by_id=by_id, by_type=by_type)
