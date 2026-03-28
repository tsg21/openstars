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


class Design(BaseModel):
    id: str
    owner: str
    name: str
    hull: str
    speed: int
    scanner_range: int


class PlanetState(BaseModel):
    id: str
    owner: str | None = None
    population: int = 0


class FleetComposition(BaseModel):
    design_id: str
    count: int


class Fleet(BaseModel):
    id: str
    owner: str
    position: Position
    composition: list[FleetComposition]
    waypoints: list[Position] = Field(default_factory=list)


class GlobalState(BaseModel):
    game: GameMeta
    players: list[Player]
    designs: list[Design]
    planets: list[PlanetState]
    fleets: list[Fleet]


# --- Player state (player-state-{username}-T{N}.json) ---


class PlayerPlanet(BaseModel):
    id: str
    name: str
    x: int
    y: int
    owner: str | None = None
    population: int | None = None


class PlayerFleet(BaseModel):
    id: str
    owner: str
    position: Position
    composition: list[FleetComposition] | None = None
    waypoints: list[Position] | None = None


class GameEvent(BaseModel):
    type: str  # "fleet_arrived" | "planet_scanned" | "fleet_detected"
    turn: int
    fleet_id: str | None = None
    fleet_name: str | None = None
    planet_id: str | None = None
    planet_name: str | None = None
    owner: str | None = None


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
