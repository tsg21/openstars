"""REST client for the OpenStars! API.

Uses the same models as the main source code. All serialisation and
deserialisation is handled here so tests can work with typed objects.
"""

import os
import time

import requests

from openstars.engine.models import (
    Galaxy,
    PlayerCommand,
    PlayerState,
)
from openstars.server.schemas import (
    CreateGameResponse,
    GameDetail,
    GameListResponse,
    ResolveResponse,
    SubmitCommandsResponse,
)

BASE_URL = os.environ.get("API_URL", "http://localhost:8080")


class GameAPIError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(f"[{status_code}] {error_code}: {message}")
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


class GameClient:
    """Typed client for one player against the running API."""

    def __init__(self, player: str | None = None, base_url: str = BASE_URL):
        self._api = f"{base_url}/api/v1"
        self._player = player

    def _headers(self) -> dict[str, str]:
        if self._player:
            return {"X-Player": self._player}
        return {}

    def _raise_for_error(self, r: requests.Response) -> None:
        if not r.ok:
            try:
                body = r.json()
                error = body.get("error", {})
                raise GameAPIError(r.status_code, error.get("code", ""), error.get("message", ""))
            except (ValueError, KeyError):
                raise GameAPIError(r.status_code, "", r.text)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def wait_for_backend(self, timeout: int = 30) -> None:
        """Block until the backend health endpoint responds."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = requests.get(f"{self._api}/health", timeout=2)
                if r.status_code == 200:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(1)
        raise TimeoutError(f"Backend not ready after {timeout}s")

    # ------------------------------------------------------------------
    # Games
    # ------------------------------------------------------------------

    def create_game(self, name: str, galaxy_size: str, players: list[str]) -> CreateGameResponse:
        r = requests.post(
            f"{self._api}/games",
            json={"name": name, "galaxy_size": galaxy_size, "players": players},
        )
        self._raise_for_error(r)
        return CreateGameResponse.model_validate(r.json())

    def list_games(self) -> GameListResponse:
        r = requests.get(f"{self._api}/games", headers=self._headers())
        self._raise_for_error(r)
        return GameListResponse.model_validate(r.json())

    def get_game(self, game_id: str) -> GameDetail:
        r = requests.get(f"{self._api}/games/{game_id}", headers=self._headers())
        self._raise_for_error(r)
        return GameDetail.model_validate(r.json())

    # ------------------------------------------------------------------
    # Play
    # ------------------------------------------------------------------

    def get_galaxy(self, game_id: str) -> Galaxy:
        r = requests.get(f"{self._api}/games/{game_id}/galaxy", headers=self._headers())
        self._raise_for_error(r)
        return Galaxy.model_validate(r.json())

    def get_state(self, game_id: str, turn: int | None = None) -> PlayerState:
        params = {"turn": turn} if turn is not None else {}
        r = requests.get(
            f"{self._api}/games/{game_id}/state",
            headers=self._headers(),
            params=params,
        )
        self._raise_for_error(r)
        return PlayerState.model_validate(r.json())

    def submit_commands(
        self, game_id: str, turn: int, commands: list[PlayerCommand]
    ) -> SubmitCommandsResponse:
        r = requests.post(
            f"{self._api}/games/{game_id}/commands",
            headers=self._headers(),
            json={
                "turn": turn,
                "commands": [c.model_dump() for c in commands],
            },
        )
        self._raise_for_error(r)
        return SubmitCommandsResponse.model_validate(r.json())

    def get_commands(self, game_id: str) -> dict:
        r = requests.get(f"{self._api}/games/{game_id}/commands", headers=self._headers())
        self._raise_for_error(r)
        return r.json()

    def resolve(self, game_id: str) -> ResolveResponse:
        r = requests.post(f"{self._api}/games/{game_id}/resolve", headers=self._headers())
        self._raise_for_error(r)
        return ResolveResponse.model_validate(r.json())
