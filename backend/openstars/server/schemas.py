"""API request/response schemas matching PRD 09."""

from datetime import datetime

from pydantic import BaseModel, Field

# --- Error responses ---


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --- Game creation ---


class CreateGameRequest(BaseModel):
    name: str
    galaxy_size: str
    players: list[str] = Field(min_length=1)
    # Defaults to False so new games are strict unless the creator opts in. The
    # GameSummary model field defaults to True instead — see the comment there.
    allow_player_override: bool = False


class PlayerInfo(BaseModel):
    username: str
    name: str


class CreateGameResponse(BaseModel):
    game_id: str
    name: str
    galaxy_size: str
    turn: int
    players: list[PlayerInfo]
    created_at: datetime


# --- Game listing ---


class GameSummaryResponse(BaseModel):
    game_id: str
    name: str
    galaxy_size: str
    turn: int
    players: list[str]
    all_turns_submitted: bool
    created_at: datetime
    allow_player_override: bool


class GameListResponse(BaseModel):
    games: list[GameSummaryResponse]


# --- Game detail ---


class PlayerSubmissionInfo(BaseModel):
    username: str
    name: str
    submitted: bool


class GameDetail(BaseModel):
    game_id: str
    name: str
    galaxy_size: str
    turn: int
    players: list[PlayerSubmissionInfo]
    created_at: datetime
    allow_player_override: bool


# --- Turn status ---


class TurnStatusResponse(BaseModel):
    turn: int
    players_awaiting_submission: list[str]


# --- Design list ---


class DesignSummaryResponse(BaseModel):
    id: str
    name: str
    hull: str
    fuel_capacity: int
    cost: dict[str, object]


class DesignSummaryResponseList(BaseModel):
    designs: list[DesignSummaryResponse]


# --- Commands ---


class SubmitCommandsRequest(BaseModel):
    turn: int
    commands: list[dict]  # Validated further in the endpoint


class SubmitCommandsResponse(BaseModel):
    status: str = "submitted"
    turn: int
    command_count: int
    turn_resolved: bool = False
    new_turn: int | None = None
