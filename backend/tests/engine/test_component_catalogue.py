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
        base_dir / "components" / "engines.yaml",
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
        base_dir / "components" / "scanners.yaml",
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
        base_dir / "components" / "weapons.yaml",
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
        base_dir / "components" / "shields.yaml",
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
        base_dir / "components" / "armour.yaml",
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
        base_dir / "components" / "electrical.yaml",
        """
schema_version: 1
components:
  - id: test_electrical
    name: Test Electrical
    component_type: electrical
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    electrical: {ability: 1}
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
    hull:
      domain: ship
      fuel_capacity: 50
      armour_points: 20
      initiative: 1
      slots:
        - slot_number: 1
          slot_categories: [engine]
          capacity: 1
          required: true
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
    assert catalogue.by_id["scout"].hull is not None
    assert catalogue.by_id["scout"].hull.domain == "ship"
    assert catalogue.by_id["scout"].hull.slots


def test_load_component_catalogue_missing_required_field(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "engines.yaml",
        """
schema_version: 1
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: components"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_groups_entries_by_component_type(
    tmp_path: Path,
) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "engines.yaml",
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
    catalogue = load_component_catalogue(tmp_path)
    assert "bad_engine" in catalogue.by_id
    assert any(entry.id == "bad_engine" for entry in catalogue.by_type["scanner"])


def test_load_component_catalogue_invalid_numeric_constraints(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "engines.yaml",
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
        tmp_path / "components" / "engines.yaml",
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
        tmp_path / "components" / "engines.yaml",
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
      slots:
        - slot_number: 1
          slot_categories: [engine]
          capacity: 1
          required: true
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
        "biotechnology": 0,
    }
    assert scout.hull is not None
    assert scout.hull.cargo_capacity == 0


def test_load_component_catalogue_defaults_missing_cost_fields(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "engines.yaml",
        """
schema_version: 1
components:
  - id: sparse_cost_engine
    name: Sparse Cost Engine
    component_type: engine
    cost: {resources: 3}
    mass: 1
    engine: {fuel_usage: [0,1,2,3,4,5,6,7,8,9], is_ramscoop: false}
  - id: free_engine
    name: Free Engine
    component_type: engine
    mass: 1
    engine: {fuel_usage: [0,1,2,3,4,5,6,7,8,9], is_ramscoop: false}
""".strip(),
    )
    catalogue = load_component_catalogue(tmp_path)

    sparse_cost = catalogue.by_id["sparse_cost_engine"].cost
    assert sparse_cost.resources == 3
    assert sparse_cost.ironium == 0
    assert sparse_cost.boranium == 0
    assert sparse_cost.germanium == 0

    free_cost = catalogue.by_id["free_engine"].cost
    assert free_cost.model_dump() == {
        "resources": 0,
        "ironium": 0,
        "boranium": 0,
        "germanium": 0,
    }


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
      slots:
        - slot_number: 1
          slot_categories: [engine]
          capacity: 1
          required: true
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"construction"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_rejects_duplicate_hull_slot_numbers(tmp_path: Path) -> None:
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
      domain: ship
      fuel_capacity: 50
      armour_points: 20
      initiative: 1
      slots:
        - slot_number: 1
          slot_categories: [engine]
          capacity: 1
          required: true
        - slot_number: 1
          slot_categories: [scanner]
          capacity: 1
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"slot_number"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_accepts_biotechnology_requirement(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "weapons.yaml",
        """
schema_version: 1
components:
  - id: test_weapon
    name: Test Weapon
    component_type: weapon
    tech_requirements: {biotechnology: 3}
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    weapon: {range: 1, damage: 1, initiative: 1}
""".strip(),
    )
    catalogue = load_component_catalogue(tmp_path)
    assert catalogue.by_id["test_weapon"].tech_requirements.biotechnology == 3


def test_load_component_catalogue_rejects_old_bio_tech_key(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "components" / "weapons.yaml",
        """
schema_version: 1
components:
  - id: test_weapon
    name: Test Weapon
    component_type: weapon
    tech_requirements: {bio_tech: 3}
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    weapon: {range: 1, damage: 1, initiative: 1}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError):
        load_component_catalogue(tmp_path)
