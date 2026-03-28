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
    players: list[str] = Field(min_length=2)


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


class GameSummary(BaseModel):
    game_id: str
    name: str
    galaxy_size: str
    turn: int
    players: list[str]
    all_turns_submitted: bool
    created_at: datetime


class GameListResponse(BaseModel):
    games: list[GameSummary]


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


# --- Commands ---


class SubmitCommandsRequest(BaseModel):
    turn: int
    commands: list[dict]  # Validated further in the endpoint


class SubmitCommandsResponse(BaseModel):
    status: str = "submitted"
    turn: int
    command_count: int


# --- Resolution ---


class ResolveResponse(BaseModel):
    turn: int
    status: str = "resolved"
