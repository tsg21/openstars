from pathlib import Path

import pytest

from openstars.engine.component_catalogue import (
    CatalogueLoadError,
    load_component_catalogue,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_all_valid_catalogue_files(base_dir: Path) -> None:
    _write_file(
        base_dir / "engines.yaml",
        """
schema_version: 1
components:
  - id: test_engine
    name: Test Engine
    component_type: engine
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {fuel_usage: [0,1,2,3,4,5,6,7,8,9], is_ramscoop: false}
""".strip(),
    )
    _write_file(
        base_dir / "scanners.yaml",
        """
schema_version: 1
components:
  - id: test_scanner
    name: Test Scanner
    component_type: scanner
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    scanner: {normal: 100, penetrating: 0}
""".strip(),
    )
    _write_file(
        base_dir / "weapons.yaml",
        """
schema_version: 1
components:
  - id: test_weapon
    name: Test Weapon
    component_type: weapon
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    weapon: {range: 1, damage: 1, initiative: 1}
""".strip(),
    )
    _write_file(
        base_dir / "shields.yaml",
        """
schema_version: 1
components:
  - id: test_shield
    name: Test Shield
    component_type: shield
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    shield: {shield_points: 1}
""".strip(),
    )
    _write_file(
        base_dir / "armour.yaml",
        """
schema_version: 1
components:
  - id: test_armour
    name: Test Armour
    component_type: armour
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    armour: {armour_points: 1}
""".strip(),
    )
    _write_file(
        base_dir / "hulls.yaml",
        """
schema_version: 1
components:
  - id: test_hull
    name: Test Hull
    component_type: hull
    cost: {resources: 10, ironium: 4, boranium: 2, germanium: 4}
    mass: 8
    hull: {fuel_capacity: 50, armour_points: 20, initiative: 1}
""".strip(),
    )


def test_load_component_catalogue_success_from_repo_data() -> None:
    base_dir = Path(__file__).resolve().parents[2] / "openstars" / "data"
    catalogue = load_component_catalogue(base_dir)
    assert "trans_galactic_drive" in catalogue.by_id
    assert len(catalogue.by_type["engine"]) >= 1
    assert "scout" in catalogue.by_id
    assert catalogue.by_id["colony_ship"].hull is not None
    assert catalogue.by_id["colony_ship"].hull.cargo_capacity == 25


def test_load_component_catalogue_missing_required_field(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: components"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_rejects_component_type_that_mismatches_filename(
    tmp_path: Path,
) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
components:
  - id: bad_engine
    name: Bad Engine
    component_type: scanner
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    scanner: {normal: 100, penetrating: 0}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: .*component_type"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_invalid_numeric_constraints(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
components:
  - id: negative_cost_engine
    name: Negative Cost Engine
    component_type: engine
    cost: {resources: -1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {fuel_usage: [0,1,2,3,4,5,6,7,8,9], is_ramscoop: false}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: .*resources"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_rejects_invalid_fuel_usage_length(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
components:
  - id: bad_fuel_len
    name: Bad Fuel Length
    component_type: engine
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {fuel_usage: [0, 1, 2], is_ramscoop: false}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"fuel_usage"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_rejects_negative_fuel_usage(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
components:
  - id: bad_fuel_value
    name: Bad Fuel Value
    component_type: engine
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {fuel_usage: [0, 1, 2, 3, 4, 5, 6, 7, 8, -1], is_ramscoop: false}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"fuel_usage"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_defaults_missing_hull_fields(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "hulls.yaml",
        """
schema_version: 1
components:
  - id: scout
    name: Scout
    component_type: hull
    cost: {resources: 10, ironium: 4, boranium: 2, germanium: 4}
    mass: 8
    hull:
      fuel_capacity: 50
      armour_points: 20
      initiative: 1
""".strip(),
    )
    catalogue = load_component_catalogue(tmp_path)
    scout = catalogue.by_id["scout"]
    assert scout.tech_requirements.model_dump() == {
        "energy": 0,
        "weapons": 0,
        "propulsion": 0,
        "construction": 0,
        "electronics": 0,
        "bio_tech": 0,
    }
    assert scout.hull is not None
    assert scout.hull.cargo_capacity == 0


def test_load_component_catalogue_rejects_negative_hull_defaults(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "hulls.yaml",
        """
schema_version: 1
components:
  - id: scout
    name: Scout
    component_type: hull
    tech_requirements:
      construction: -1
    cost: {resources: 10, ironium: 4, boranium: 2, germanium: 4}
    mass: 8
    hull:
      fuel_capacity: 50
      armour_points: 20
      initiative: 1
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"construction"):
        load_component_catalogue(tmp_path)
