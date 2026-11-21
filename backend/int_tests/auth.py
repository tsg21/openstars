"""Mint Firebase ID tokens from the auth emulator for integration tests.

Every player-scoped endpoint takes identity from a verified Google ID token
(PRD 04), so the integration suite needs real tokens rather than the old
``X-Player`` header. The Firebase auth emulator will issue one for any email
via its Identity Toolkit REST surface, and the backend — which runs with
``FIREBASE_AUTH_EMULATOR_HOST`` set — verifies it without a signature check.

Requires the emulator from ``int_tests/docker-compose.yaml`` to be running.
"""

import json
import os
import urllib.parse

import requests

# The host address of the auth emulator, as seen from the test process. The
# backend container reaches the same emulator on its compose service name.
AUTH_EMULATOR_HOST = os.environ.get("AUTH_EMULATOR_HOST", "localhost:9099")

# The emulator accepts any API key; it never validates it.
_FAKE_API_KEY = "fake-api-key"

_SIGN_IN_URL = (
    f"http://{AUTH_EMULATOR_HOST}"
    f"/identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={_FAKE_API_KEY}"
)

# Tokens are valid for an hour and the suite runs in minutes, so one sign-in per
# email is enough. Repeated sign-ins for the same email reuse the emulator's
# existing account, which would otherwise be a needless round-trip per request.
_tokens: dict[str, str] = {}


class AuthEmulatorError(RuntimeError):
    """The auth emulator refused to issue a token."""


def id_token_for(email: str) -> str:
    """Return a verified-email Google ID token for ``email``."""
    if email not in _tokens:
        _tokens[email] = _sign_in_with_google(email)
    return _tokens[email]


def _sign_in_with_google(email: str) -> str:
    """Sign in through the emulator's fake Google provider.

    ``email_verified`` has to be asserted here: ``get_current_identity`` rejects
    a token without it, and the emulator's plain password sign-up path leaves
    the address unverified.
    """
    claims = json.dumps({"sub": f"google-{email}", "email": email, "email_verified": True})
    body = {
        "postBody": urllib.parse.urlencode({"id_token": claims, "providerId": "google.com"}),
        "requestUri": "http://localhost",
        "returnSecureToken": True,
    }

    try:
        response = requests.post(_SIGN_IN_URL, json=body, timeout=10)
    except requests.RequestException as exc:
        raise AuthEmulatorError(
            f"Could not reach the auth emulator at {AUTH_EMULATOR_HOST}. "
            "Start it with int_tests/run_docker.sh or int_tests/run.sh."
        ) from exc

    if not response.ok:
        raise AuthEmulatorError(
            f"Sign-in for {email!r} failed: [{response.status_code}] {response.text}"
        )

    token = response.json().get("idToken")
    if not token:
        raise AuthEmulatorError(f"Sign-in for {email!r} returned no idToken: {response.text}")
    return token
