"""REST client for the OpenStars! API.

Uses the same models as the main source code. All serialisation and
deserialisation is handled here so tests can work with typed objects.
"""

import os
import time

import requests
from auth import id_token_for

from openstars.engine.models import (
    Galaxy,
    PlayerCommand,
    PlayerState,
    SelectRaceCommand,
)
from openstars.server.schemas import (
    CreateGameResponse,
    GameDetail,
    GameListResponse,
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
    """Typed client for one player against the running API.

    ``player`` is the player's Google email — the identity the API takes from a
    verified ID token. Omit it for an unauthenticated client, which every
    player-scoped route answers with 401.

    ``override`` names a different participant to play as. It is sent as the
    ``X-Player`` header and is honoured only on games created with
    ``allow_player_override=True``.
    """

    def __init__(
        self,
        player: str | None = None,
        base_url: str = BASE_URL,
        override: str | None = None,
    ):
        self._api = f"{base_url}/api/v1"
        self._player = player
        self._override = override

    def _headers(self) -> dict[str, str]:
        if not self._player:
            return {}
        headers = {"Authorization": f"Bearer {id_token_for(self._player)}"}
        if self._override:
            headers["X-Player"] = self._override
        return headers

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

    def create_game(
        self,
        name: str,
        galaxy_size: str,
        players: list[str],
        allow_player_override: bool = False,
    ) -> CreateGameResponse:
        r = requests.post(
            f"{self._api}/games",
            headers=self._headers(),
            json={
                "name": name,
                "galaxy_size": galaxy_size,
                "players": players,
                "allow_player_override": allow_player_override,
            },
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
                "commands": [c.model_dump(mode="json") for c in commands],
            },
        )
        self._raise_for_error(r)
        return SubmitCommandsResponse.model_validate(r.json())

    def get_commands(self, game_id: str) -> dict:
        r = requests.get(f"{self._api}/games/{game_id}/commands", headers=self._headers())
        self._raise_for_error(r)
        return r.json()

    def select_humanoid_race(self, game_id: str) -> SubmitCommandsResponse:
        return self.submit_commands(
            game_id,
            turn=0,
            commands=[SelectRaceCommand(predefined_id="humanoid")],
        )

    def preview_race(self, race: dict) -> dict:
        r = requests.post(
            f"{self._api}/race/preview",
            headers=self._headers(),
            json={"race": race},
        )
        self._raise_for_error(r)
        return r.json()

    def get_race(self, game_id: str) -> dict:
        r = requests.get(f"{self._api}/games/{game_id}/race", headers=self._headers())
        self._raise_for_error(r)
        return r.json()

    def get_predefined_races(self) -> list[dict]:
        r = requests.get(f"{self._api}/race/predefined", headers=self._headers())
        self._raise_for_error(r)
        return r.json()

    # ------------------------------------------------------------------
    # Ship designs
    # ------------------------------------------------------------------

    def create_ship_design(
        self,
        game_id: str,
        *,
        name: str,
        hull: str,
        components: list[dict],
    ) -> dict:
        r = requests.post(
            f"{self._api}/games/{game_id}/designs",
            headers=self._headers(),
            json={"name": name, "hull": hull, "components": components},
        )
        self._raise_for_error(r)
        return r.json()["design"]
