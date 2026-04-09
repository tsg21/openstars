"""Component catalogue models and YAML loader for designer APIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

ComponentType = Literal["engine", "scanner", "weapon", "shield", "armour"]

COMPONENT_TYPE_FILENAMES: dict[ComponentType, str] = {
    "engine": "engines.yaml",
    "scanner": "scanners.yaml",
    "weapon": "weapons.yaml",
    "shield": "shields.yaml",
    "armour": "armour.yaml",
}


class CatalogueLoadError(RuntimeError):
    """Raised when component catalogue files fail to parse or validate."""


class ComponentCost(BaseModel):
    resources: int = Field(ge=0)
    ironium: int = Field(ge=0)
    boranium: int = Field(ge=0)
    germanium: int = Field(ge=0)


class EngineStats(BaseModel):
    max_warp: int = Field(ge=1)
    is_ramscoop: bool = False


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


class ComponentCatalogueEntry(BaseModel):
    id: str
    name: str
    component_type: ComponentType
    cost: ComponentCost
    mass: int = Field(ge=0)
    engine: EngineStats | None = None
    scanner: ScannerStats | None = None
    weapon: WeaponStats | None = None
    shield: ShieldStats | None = None
    armour: ArmourStats | None = None

    @model_validator(mode="after")
    def validate_stats(self) -> ComponentCatalogueEntry:
        return self


class ComponentCatalogueDocument(BaseModel):
    schema_version: int
    component_type: ComponentType
    components: list[ComponentCatalogueEntry]

    @model_validator(mode="after")
    def validate_component_type_stats(self) -> ComponentCatalogueDocument:
        stat_field_by_type: dict[ComponentType, str] = {
            "engine": "engine",
            "scanner": "scanner",
            "weapon": "weapon",
            "shield": "shield",
            "armour": "armour",
        }
        expected_field = stat_field_by_type[self.component_type]
        for entry in self.components:
            if entry.component_type != self.component_type:
                raise ValueError(
                    f"component {entry.id!r} has component_type {entry.component_type!r} "
                    f"but document component_type is {self.component_type!r}"
                )
            present_fields = [
                field_name
                for field_name in stat_field_by_type.values()
                if getattr(entry, field_name) is not None
            ]
            if present_fields != [expected_field]:
                raise ValueError(
                    f"component {entry.id!r} must define exactly one stats block "
                    f"for {self.component_type!r}, found {present_fields}"
                )
        return self


@dataclass(frozen=True)
class ComponentCatalogue:
    """Loaded component catalogue indexed by ID and type."""

    by_id: dict[str, ComponentCatalogueEntry]
    by_type: dict[ComponentType, list[ComponentCatalogueEntry]]


def _data_components_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "components"


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
    components_dir = base_dir or _data_components_dir()
    by_id: dict[str, ComponentCatalogueEntry] = {}
    by_type: dict[ComponentType, list[ComponentCatalogueEntry]] = {
        component_type: [] for component_type in COMPONENT_TYPE_FILENAMES
    }

    for component_type in sorted(COMPONENT_TYPE_FILENAMES):
        filename = COMPONENT_TYPE_FILENAMES[component_type]
        path = components_dir / filename
        if not path.exists():
            raise CatalogueLoadError(f"{filename}: expected file is missing")
        document = _load_one_document(path)
        if document.component_type != component_type:
            raise CatalogueLoadError(
                f"{filename}: component_type {document.component_type!r} does not "
                f"match file type {component_type!r}"
            )
        for index, component in enumerate(document.components):
            if component.id in by_id:
                raise CatalogueLoadError(
                    f"{filename}: components[{index}] duplicate id {component.id!r}"
                )
            by_id[component.id] = component
            by_type[component_type].append(component)

    return ComponentCatalogue(by_id=by_id, by_type=by_type)
