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
component_type: engine
components:
  - id: test_engine
    name: Test Engine
    component_type: engine
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {max_warp: 5, is_ramscoop: false}
""".strip(),
    )
    _write_file(
        base_dir / "scanners.yaml",
        """
schema_version: 1
component_type: scanner
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
component_type: weapon
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
component_type: shield
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
component_type: armour
components:
  - id: test_armour
    name: Test Armour
    component_type: armour
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    armour: {armour_points: 1}
""".strip(),
    )


def test_load_component_catalogue_success_from_repo_data() -> None:
    base_dir = Path(__file__).resolve().parents[2] / "openstars" / "data" / "components"
    catalogue = load_component_catalogue(base_dir)
    assert "trans_galactic_drive" in catalogue.by_id
    assert len(catalogue.by_type["engine"]) >= 1


def test_load_component_catalogue_missing_required_field(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
component_type: engine
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: components"):
        load_component_catalogue(tmp_path)


def test_load_component_catalogue_invalid_component_type_enum(tmp_path: Path) -> None:
    _write_all_valid_catalogue_files(tmp_path)
    _write_file(
        tmp_path / "engines.yaml",
        """
schema_version: 1
component_type: engine
components:
  - id: bad_engine
    name: Bad Engine
    component_type: scanner
    cost: {resources: 1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {max_warp: 5, is_ramscoop: false}
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
component_type: engine
components:
  - id: negative_cost_engine
    name: Negative Cost Engine
    component_type: engine
    cost: {resources: -1, ironium: 0, boranium: 0, germanium: 0}
    mass: 1
    engine: {max_warp: 5, is_ramscoop: false}
""".strip(),
    )
    with pytest.raises(CatalogueLoadError, match=r"engines.yaml: .*resources"):
        load_component_catalogue(tmp_path)
