"""Entity ID generator using a Feistel cipher (PRD 04).

Format: 2-char uppercase prefix + 6-char lowercase base36 suffix.
The Feistel cipher maps a sequential counter to a random-looking but
deterministic and collision-free ID, keyed by the game seed.
"""

import hashlib
import struct

# Base36 alphabet: 0-9 + a-z → 36 chars
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_BASE = 36

# The Feistel cipher operates on the 6-char base36 space.
# 36^6 = 2,176,782,336 (~2.18 billion values).
# We split this into two halves: 36^3 = 46,656 each.
_HALF_MOD = _BASE**3  # 46656
_ROUNDS = 4


def _round_function(half: int, round_num: int, seed: int) -> int:
    """Feistel round function: hash half + round + seed → value in [0, HALF_MOD)."""
    data = struct.pack(">IIQ", half, round_num, seed)
    digest = hashlib.sha256(data).digest()
    # Take first 4 bytes as unsigned int, mod HALF_MOD
    val = struct.unpack(">I", digest[:4])[0]
    return val % _HALF_MOD


def _feistel_encrypt(counter: int, seed: int) -> int:
    """Encrypt a counter value through the Feistel network.

    Input and output are in [0, 36^6).
    """
    # Split counter into left and right halves
    left = counter // _HALF_MOD
    right = counter % _HALF_MOD

    for round_num in range(_ROUNDS):
        new_left = right
        new_right = (left + _round_function(right, round_num, seed)) % _HALF_MOD
        left = new_left
        right = new_right

    return left * _HALF_MOD + right


def _to_base36(value: int, length: int = 6) -> str:
    """Encode an integer as a fixed-length base36 string (lowercase)."""
    chars = []
    for _ in range(length):
        chars.append(_ALPHABET[value % _BASE])
        value //= _BASE
    return "".join(reversed(chars))


def create_id(next_id: int, seed: int, prefix: str) -> str:
    """Create an entity ID.

    Args:
        next_id: Current counter value.
        seed: Game seed for the Feistel cipher.
        prefix: 2-char uppercase prefix (PL, FL, DE).

    Returns:
        entity_id
    """
    if len(prefix) != 2 or prefix != prefix.upper():
        raise ValueError(f"Prefix must be 2 uppercase chars, got: {prefix!r}")

    max_counter = _BASE**6  # 2,176,782,336
    if next_id >= max_counter:
        raise ValueError(f"Counter overflow: {next_id} >= {max_counter}")

    encrypted = _feistel_encrypt(next_id, seed)
    suffix = _to_base36(encrypted)
    return f"{prefix}{suffix}"

def allocate_id(next_id: int, seed: int, prefix: str) -> tuple[str, int]:
    return create_id(next_id, seed, prefix), next_id + 1
