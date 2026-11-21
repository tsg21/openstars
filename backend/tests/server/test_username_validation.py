"""Unit tests for username validation on game creation.

Under the sign-in gate a username *is* the authenticated Google email (PRD 04),
so the character set has to admit `@` and `+` without letting path-traversal or
URL-breaking characters back in.
"""

import pytest

from openstars.server.routes.games import _validate_usernames

ACCEPTED = [
    "tim",
    "player1",
    "tim.gage",
    "tim-gage",
    "tim_gage",
    "alice@example.com",
    "alice+openstars@example.com",
    "first.last+tag@sub.example.co.uk",
    "9lives",
    "a" * 64,
]

REJECTED = [
    "",
    "../../etc/passwd",
    ".hidden",
    "-leading-dash",
    "+leading-plus",
    "@leading-at",
    "with space@example.com",
    "with/slash",
    "with\\backslash",
    "with:colon",
    "with%20encoded",
    "with#hash",
    "with?query",
    "a" * 65,
    "a" * 60 + "@example.com",  # 72 chars — over the limit despite valid characters
]


@pytest.mark.parametrize("username", ACCEPTED)
def test_accepts_valid_username(username):
    assert _validate_usernames([username]) is None


@pytest.mark.parametrize("username", REJECTED)
def test_rejects_invalid_username(username):
    result = _validate_usernames([username])
    assert result is not None
    assert result.status_code == 400


def test_rejects_when_any_username_in_the_list_is_invalid():
    result = _validate_usernames(["alice@example.com", "../../etc/passwd"])
    assert result is not None
    assert result.status_code == 400


def test_accepts_a_mixed_list_of_emails_and_legacy_names():
    """Override games keep free-text usernames alongside email identities."""
    assert _validate_usernames(["alice@example.com", "tim", "matt"]) is None


def test_error_message_lists_the_permitted_characters():
    result = _validate_usernames(["with space"])
    assert result is not None
    message = result.body.decode()
    for char in (".", "-", "_", "+", "@"):
        assert char in message
