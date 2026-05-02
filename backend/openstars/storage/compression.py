"""Helpers for gzip-compressed JSON blobs."""

from gzip import BadGzipFile, compress, decompress

BLOB_SUFFIX = ".json.gz"


def encode_json(payload: str) -> bytes:
    """Encode a JSON string to deterministic gzip bytes."""
    return compress(payload.encode("utf-8"), compresslevel=6, mtime=0)


def decode_json(data: bytes) -> str:
    """Decode gzip-compressed JSON bytes."""
    try:
        return decompress(data).decode("utf-8")
    except BadGzipFile as exc:
        raise ValueError("Invalid gzip-compressed JSON payload") from exc
