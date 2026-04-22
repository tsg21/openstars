"""Derive Altair combat tokens from engine ``Fleet`` + ``Design`` data.

Lives outside ``openstars.combat.altair`` so the altair package can stay
self-contained (it may not import engine models or the catalogue directly).
"""

from __future__ import annotations

from openstars.combat.altair.models import Position, Token, TokenWeapon
from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.models import Design, Fleet


def _design_weapons(
    design: Design,
    catalogue: ComponentCatalogue,
    ship_count: int,
) -> list[TokenWeapon]:
    """Aggregate identical beam-weapon components across slots.

    Non-beam weapons are skipped for v1 — no such entries exist in the
    catalogue yet, but the guard keeps the engine honest as it grows.
    """
    counts: dict[str, int] = {}
    for component in design.components:
        entry = catalogue.by_id.get(component.component_id)
        if entry is None or entry.component_type != "weapon" or entry.weapon is None:
            continue
        counts[component.component_id] = (
            counts.get(component.component_id, 0) + component.component_count
        )

    weapons: list[TokenWeapon] = []
    for component_id, slot_count in counts.items():
        entry = catalogue.by_id[component_id]
        assert entry.weapon is not None
        weapons.append(
            TokenWeapon(
                component_id=component_id,
                weapon_type="beam",
                count=slot_count * ship_count,
                damage=entry.weapon.damage,
                range_classic=entry.weapon.range,
                initiative=entry.weapon.initiative,
            )
        )
    weapons.sort(key=lambda w: w.component_id)
    return weapons


def _design_hp_per_ship(design: Design, catalogue: ComponentCatalogue) -> int:
    """Hull armour + summed armour-component points for a single ship."""
    hull_entry = catalogue.by_id.get(design.hull)
    base = hull_entry.hull.armour_points if hull_entry and hull_entry.hull else 0
    armour = 0
    for component in design.components:
        entry = catalogue.by_id.get(component.component_id)
        if entry is None or entry.component_type != "armour" or entry.armour is None:
            continue
        armour += entry.armour.armour_points * component.component_count
    return base + armour


def tokens_from_fleet(
    fleet: Fleet,
    designs_by_id: dict[str, Design],
    catalogue: ComponentCatalogue,
    *,
    position: Position | None = None,
    token_id_prefix: str | None = None,
) -> list[Token]:
    """Build one ``Token`` per ``FleetComposition`` entry in *fleet*.

    ``position`` is the starting coordinate in the *arena* (scaled by ``S``),
    not the fleet's galactic position. The battle-setup layer decides where
    each side enters the arena; this helper just materialises tokens. All
    tokens from one fleet share the same starting position.

    Entries whose ``design_id`` is not present in ``designs_by_id`` are
    skipped silently so stale or partially-loaded state cannot abort a
    battle.
    """
    tokens: list[Token] = []
    prefix = token_id_prefix or "t"
    arena_position = position if position is not None else Position(x=0, y=0)
    for index, entry in enumerate(fleet.composition):
        design = designs_by_id.get(entry.design_id)
        if design is None:
            continue
        weapons = _design_weapons(design, catalogue, entry.count)
        hp = _design_hp_per_ship(design, catalogue) * entry.count
        tokens.append(
            Token(
                id=f"{prefix}-{fleet.id}-{index}",
                owner=fleet.owner,
                position=arena_position.model_copy(),
                hp=hp,
                design_id=entry.design_id,
                ship_count=entry.count,
                weapons=weapons,
                label=fleet.name,
            )
        )
    return tokens
