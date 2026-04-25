"""Game state models matching PRDs 05, 07, 12, 13, and 14."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

STATE_VERSION = 1
RESEARCH_FIELDS: tuple[str, ...] = (
    "energy",
    "weapons",
    "propulsion",
    "construction",
    "electronics",
    "biotechnology",
)

# --- Shared primitives ---


class Position(BaseModel):
    x: int
    y: int


# --- Galaxy (galaxy.json) ---


class GalaxyMetadata(BaseModel):
    name: str
    size: str  # "small" | "medium" | "large" | "huge"
    seed: int


class GalaxyPlanet(BaseModel):
    id: str
    name: str
    x: int
    y: int


class Galaxy(BaseModel):
    galaxy: GalaxyMetadata
    planets: list[GalaxyPlanet]


# --- Global state (global-state-T{N}.json) ---


class GameMeta(BaseModel):
    seed: int
    turn: int
    next_id: int
    combat_ruleset: Literal["altair", "classic"] = "altair"


class PlayerResearchState(BaseModel):
    levels: dict[str, int]
    progress: dict[str, int]
    current_field: str
    next_field: str | None = None
    allocation_percent: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_research(self) -> "PlayerResearchState":
        expected_fields = set(RESEARCH_FIELDS)
        if set(self.levels.keys()) != expected_fields:
            raise ValueError("levels must include exactly the six canonical research fields")
        if set(self.progress.keys()) != expected_fields:
            raise ValueError("progress must include exactly the six canonical research fields")
        if self.current_field not in expected_fields:
            raise ValueError("current_field must be one of the canonical research fields")
        if self.next_field is not None and self.next_field not in expected_fields:
            raise ValueError("next_field must be one of the canonical research fields")
        for field_name, level in self.levels.items():
            if level < 0 or level > 26:
                raise ValueError(f"levels.{field_name} must be in range 0..26")
        for field_name, value in self.progress.items():
            if value < 0:
                raise ValueError(f"progress.{field_name} must be >= 0")
        return self


def default_research_state() -> PlayerResearchState:
    return PlayerResearchState(
        levels={field: 0 for field in RESEARCH_FIELDS},
        progress={field: 0 for field in RESEARCH_FIELDS},
        current_field="energy",
        next_field=None,
        allocation_percent=15,
    )


class Player(BaseModel):
    username: str
    name: str
    research_state: PlayerResearchState = Field(default_factory=default_research_state)


class Scanner(BaseModel):
    normal: int  # normal (non-penetrating) range in light-years; 0 = no scanner
    penetrating: int = 0  # penetrating range in light-years; always <= normal


class DesignComponent(BaseModel):
    slot_number: int = Field(ge=1)
    component_id: str
    component_count: int = Field(ge=1)


class Design(BaseModel):
    id: str
    owner: str
    name: str
    hull: str
    components: list[DesignComponent] = Field(default_factory=list)
    mass: int = Field(default=0, gt=0)
    fuel_usage: list[int] = Field(default_factory=lambda: [0] * 10)
    fuel_capacity: int = Field(ge=0)
    scanner: Scanner
    cargo_capacity: int = Field(default=0, ge=0)
    cost: "DesignCost"

    @model_validator(mode="after")
    def validate_fuel_usage(self) -> "Design":
        if len(self.fuel_usage) != 10:
            raise ValueError("fuel_usage must contain exactly 10 entries (warp 1..10)")
        return self


class DesignCost(BaseModel):
    resources: int = Field(ge=0)
    minerals: "Minerals" = Field(default_factory=lambda: Minerals())


class Minerals(BaseModel):
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0


class Habitability(BaseModel):
    gravity: int = 0
    temperature: int = 0
    radiation: int = 0


class ProductionProgress(BaseModel):
    resources_spent: int = 0
    minerals_spent: Minerals = Field(default_factory=Minerals)


StarbaseType = Literal["orbital_fort", "space_station"]


class PlanetStarbaseState(BaseModel):
    type: StarbaseType
    can_build_ships: bool


class ProductionQueueItem(BaseModel):
    id: str
    item_type: Literal["mine", "factory", "starbase", "ship", "planetary_scanner"]
    target_type: StarbaseType | None = None
    design_id: str | None = None
    quantity: int = Field(gt=0)
    progress: ProductionProgress = Field(default_factory=ProductionProgress)

    @model_validator(mode="after")
    def validate_target_type(self) -> "ProductionQueueItem":
        if self.item_type == "starbase":
            if self.target_type is None:
                raise ValueError("starbase production items require target_type")
        elif self.target_type is not None:
            raise ValueError("target_type is only valid for starbase production items")
        if self.item_type == "ship":
            if self.design_id is None:
                raise ValueError("ship production items require design_id")
        elif self.design_id is not None:
            raise ValueError("design_id is only valid for ship production items")
        if self.item_type == "planetary_scanner" and self.quantity != 1:
            raise ValueError("planetary_scanner production quantity must be exactly 1")
        return self


class PlanetState(BaseModel):
    id: str
    owner: str | None = None
    population: int = 0
    mines: int = 0
    factories: int = 0
    minerals: Minerals = Field(default_factory=Minerals)
    concentrations: Minerals = Field(default_factory=Minerals)
    mine_years: Minerals = Field(default_factory=Minerals)
    is_homeworld: bool = False
    production_queue: list[ProductionQueueItem] = Field(default_factory=list)
    habitability: Habitability = Field(default_factory=Habitability)
    starbase: PlanetStarbaseState | None = None
    has_scanner: bool = False
    contribute_only_leftover_to_research: bool = False


class FleetComposition(BaseModel):
    design_id: str
    count: int


class Cargo(BaseModel):
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0
    colonists: int = 0


class CargoOrder(BaseModel):
    cargo_type: Literal["ironium", "boranium", "germanium", "colonists"]
    action: Literal[
        "load_all",
        "load_amount",
        "load_up_to",
        "unload_all",
        "unload_amount",
        "unload_but",
    ]
    amount: int | None = None


class WaypointTask(BaseModel):
    type: Literal["transport", "transfer", "colonise"]
    orders: list[CargoOrder] = Field(default_factory=list)
    fleet_id: str | None = None


class Waypoint(BaseModel):
    x: int
    y: int
    warp: int | None = Field(default=None, ge=1, le=10)
    task: WaypointTask | None = None


class Fleet(BaseModel):
    id: str
    name: str
    owner: str
    position: Position
    composition: list[FleetComposition]
    cargo: Cargo = Field(default_factory=Cargo)
    fuel: int = 0
    repeat: bool = False
    waypoints: list[Waypoint] = Field(default_factory=list)
    bearing: float | None = None


class GameEvent(BaseModel):
    owner: str
    source_id: str | None = None
    code: str
    values: list[str | int] = Field(default_factory=list)


class GlobalState(BaseModel):
    state_version: int = STATE_VERSION
    game: GameMeta
    players: list[Player]
    planets: list[PlanetState]
    fleets: list[Fleet]
    events: dict[str, list[GameEvent]] = Field(default_factory=dict)
    planet_resources: dict[str, int] = Field(default_factory=dict)
    pop_growth: dict[str, int] = Field(default_factory=dict)


# --- Player state (player-state-{username}-T{N}.json) ---


class PlayerPlanet(BaseModel):
    id: str
    name: str
    x: int
    y: int
    owner: str | None = None
    population: int | None = None
    scan_level: str = "none"  # "none" | "basic" | "detailed"
    scan_age: int = 0
    mines: int | None = None
    factories: int | None = None
    minerals: Minerals | None = None
    concentrations: Minerals | None = None
    resources: int | None = None
    mining_rate: Minerals | None = None
    production_queue: list["PlayerProductionQueueItem"] | None = None
    habitability: "Habitability | None" = None
    max_population: int | None = None
    pop_growth: int | None = None
    starbase: "PlayerPlanetStarbaseState | PlayerPlanetStarbaseSummary | None" = None
    scanner: "PlayerPlanetScannerState | PlayerPlanetScannerSummary | None" = None
    contribute_only_leftover_to_research: bool | None = None


class PlayerPlanetStarbaseState(BaseModel):
    type: StarbaseType
    can_build_ships: bool


class PlayerPlanetStarbaseSummary(BaseModel):
    present: bool
    type: StarbaseType | None = None
    can_build_ships: bool | None = None


class PlayerPlanetScannerState(BaseModel):
    installed: bool
    name: str
    normal: int
    penetrating: int


class PlayerPlanetScannerSummary(BaseModel):
    installed: bool


class PlayerProductionQueueItem(BaseModel):
    id: str
    item_type: Literal["mine", "factory", "starbase", "ship", "planetary_scanner"]
    target_type: StarbaseType | None = None
    design_id: str | None = None
    quantity: int = Field(gt=0)
    progress: ProductionProgress = Field(default_factory=ProductionProgress)

    @model_validator(mode="after")
    def validate_target_type(self) -> "PlayerProductionQueueItem":
        if self.item_type == "starbase":
            if self.target_type is None:
                raise ValueError("starbase production items require target_type")
        elif self.target_type is not None:
            raise ValueError("target_type is only valid for starbase production items")
        if self.item_type == "ship":
            if self.design_id is None:
                raise ValueError("ship production items require design_id")
        elif self.design_id is not None:
            raise ValueError("design_id is only valid for ship production items")
        if self.item_type == "planetary_scanner" and self.quantity != 1:
            raise ValueError("planetary_scanner production quantity must be exactly 1")
        return self


class PlayerFleet(BaseModel):
    id: str
    name: str | None = None
    owner: str
    position: Position
    composition: list[FleetComposition] | None = None
    waypoints: list[Waypoint] | None = None
    cargo: Cargo | None = None
    cargo_capacity: int | None = None
    fuel: int | None = None
    fuel_capacity: int | None = None
    bearing: float | None = None  # degrees, 0=north clockwise; None if stationary


class PlayerStateResearch(BaseModel):
    levels: dict[str, int]
    progress: dict[str, int]
    current_field: str
    next_field: str | None = None
    allocation_percent: int
    current_field_remaining_cost: int
    estimated_resources_this_turn: int


class PlayerState(BaseModel):
    state_version: int = STATE_VERSION
    player: str
    turn: int
    planets: list[PlayerPlanet]
    fleets: list[PlayerFleet]
    designs: list[Design]
    events: list[GameEvent] = Field(default_factory=list)
    research: PlayerStateResearch | None = None


# --- Player commands (player-command-{username}-T{N}.json) ---


class SetWaypointsCommand(BaseModel):
    type: Literal["set_waypoints"] = "set_waypoints"
    fleet_id: str
    waypoints: list[Waypoint]
    repeat: bool | None = None


class RenameFleetCommand(BaseModel):
    type: Literal["rename_fleet"] = "rename_fleet"
    fleet_id: str
    name: str = Field(min_length=1, max_length=64)


class JettisonCargoCommand(BaseModel):
    type: Literal["jettison_cargo"] = "jettison_cargo"
    fleet_id: str
    cargo: Cargo


class MergeSplitFleetEntry(BaseModel):
    fleet_id: str
    name: str | None = None
    ships: list[FleetComposition]


class MergeSplitFleetsCommand(BaseModel):
    type: Literal["merge_split_fleets"] = "merge_split_fleets"
    fleets: list[MergeSplitFleetEntry]


class AddProductionItemCommand(BaseModel):
    type: Literal["add_production_item"] = "add_production_item"
    planet_id: str
    item_type: Literal["mine", "factory", "starbase", "ship", "planetary_scanner"]
    target_type: StarbaseType | None = None
    design_id: str | None = None
    quantity: int = Field(gt=0)
    insert_after_item_id: str | None = None

    @model_validator(mode="after")
    def validate_target_type(self) -> "AddProductionItemCommand":
        if self.item_type == "starbase":
            if self.target_type is None:
                raise ValueError("starbase production items require target_type")
        elif self.target_type is not None:
            raise ValueError("target_type is only valid for starbase production items")
        if self.item_type == "ship":
            if self.design_id is None:
                raise ValueError("ship production items require design_id")
        elif self.design_id is not None:
            raise ValueError("design_id is only valid for ship production items")
        if self.item_type == "planetary_scanner" and self.quantity != 1:
            raise ValueError("planetary_scanner production quantity must be exactly 1")
        return self


class MoveProductionItemCommand(BaseModel):
    type: Literal["move_production_item"] = "move_production_item"
    planet_id: str
    item_id: str
    insert_after_item_id: str | None = None


class RemoveProductionItemCommand(BaseModel):
    type: Literal["remove_production_item"] = "remove_production_item"
    planet_id: str
    item_id: str
    quantity: int = Field(gt=0)


class ClearProductionQueueCommand(BaseModel):
    type: Literal["clear_production_queue"] = "clear_production_queue"
    planet_id: str


class SetResearchCommand(BaseModel):
    type: Literal["set_research"] = "set_research"
    current_field: str | None = None
    next_field: str | None = None
    allocation_percent: int | None = None

    @model_validator(mode="after")
    def validate_research_fields(self) -> "SetResearchCommand":
        if self.current_field is not None and self.current_field not in RESEARCH_FIELDS:
            raise ValueError("current_field must be one of the canonical research fields")
        if self.next_field is not None and self.next_field not in RESEARCH_FIELDS:
            raise ValueError("next_field must be one of the canonical research fields")
        if self.allocation_percent is not None and (
            self.allocation_percent < 0 or self.allocation_percent > 100
        ):
            raise ValueError("allocation_percent must be in range 0..100")
        return self


class SetPlanetProductionModeCommand(BaseModel):
    type: Literal["set_planet_production_mode"] = "set_planet_production_mode"
    planet_id: str
    contribute_only_leftover_to_research: bool


PlayerCommand = Annotated[
    SetWaypointsCommand
    | RenameFleetCommand
    | JettisonCargoCommand
    | MergeSplitFleetsCommand
    | AddProductionItemCommand
    | MoveProductionItemCommand
    | RemoveProductionItemCommand
    | ClearProductionQueueCommand
    | SetResearchCommand
    | SetPlanetProductionModeCommand,
    Field(discriminator="type"),
]


class PlayerCommands(BaseModel):
    commands: list[PlayerCommand]
