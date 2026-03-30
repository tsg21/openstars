"""Game state models matching PRDs 05, 07, and the player state schema."""

from pydantic import BaseModel, Field

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


class Player(BaseModel):
    username: str
    name: str


class Scanner(BaseModel):
    normal: int  # normal (non-penetrating) range in parsecs; 0 = no scanner
    penetrating: int = 0  # penetrating range in parsecs; always <= normal


class Design(BaseModel):
    id: str
    owner: str
    name: str
    hull: str
    speed: int
    scanner: Scanner


class Minerals(BaseModel):
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0


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


class FleetComposition(BaseModel):
    design_id: str
    count: int


class Fleet(BaseModel):
    id: str
    owner: str
    position: Position
    composition: list[FleetComposition]
    waypoints: list[Position] = Field(default_factory=list)


class GameEvent(BaseModel):
    type: str  # "fleet_arrived" | "planet_scanned" | "fleet_detected" | "mining_complete"
    turn: int
    fleet_id: str | None = None
    fleet_name: str | None = None
    planet_id: str | None = None
    planet_name: str | None = None
    owner: str | None = None
    ironium: int | None = None
    boranium: int | None = None
    germanium: int | None = None


class GlobalState(BaseModel):
    game: GameMeta
    players: list[Player]
    designs: list[Design]
    planets: list[PlanetState]
    fleets: list[Fleet]
    events: dict[str, list[GameEvent]] = Field(default_factory=dict)
    planet_resources: dict[str, int] = Field(default_factory=dict)


# --- Player state (player-state-{username}-T{N}.json) ---


class PlayerPlanet(BaseModel):
    id: str
    name: str
    x: int
    y: int
    owner: str | None = None
    population: int | None = None
    scan_level: str = "none"  # "none" | "basic" | "detailed"
    mines: int | None = None
    factories: int | None = None
    minerals: Minerals | None = None
    concentrations: Minerals | None = None
    resources: int | None = None
    mining_rate: Minerals | None = None


class PlayerFleet(BaseModel):
    id: str
    owner: str
    position: Position
    composition: list[FleetComposition] | None = None
    waypoints: list[Position] | None = None
    bearing: float | None = None  # degrees, 0=north clockwise; None if stationary


class PlayerState(BaseModel):
    player: str
    turn: int
    planets: list[PlayerPlanet]
    fleets: list[PlayerFleet]
    designs: list[Design]
    events: list[GameEvent] = Field(default_factory=list)


# --- Player commands (player-command-{username}-T{N}.json) ---


class SetWaypointsCommand(BaseModel):
    type: str = "set_waypoints"
    fleet_id: str
    waypoints: list[Position]


class PlayerCommands(BaseModel):
    commands: list[SetWaypointsCommand]
