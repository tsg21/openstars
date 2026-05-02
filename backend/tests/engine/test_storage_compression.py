import pytest

from openstars.storage.compression import decode_json, encode_json


def test_round_trip_json_payload() -> None:
    payload = '{"state_version":1,"game":{"turn":0},"players":[{"username":"tim"}]}'
    assert decode_json(encode_json(payload)) == payload


def test_encoding_is_deterministic() -> None:
    payload = '{"repeat":[1,2,3,4],"name":"OpenStars"}'
    assert encode_json(payload) == encode_json(payload)


def test_decode_rejects_non_gzip_input() -> None:
    with pytest.raises(ValueError, match="Invalid gzip-compressed JSON payload"):
        decode_json(b'{"not": "gzipped"}')


def test_compression_reduces_typical_state_payload_size() -> None:
    repeated = '{"planet":"Sol","owner":"tim","population":25000}'
    payload = "[" + ",".join([repeated] * 200) + "]"
    assert len(encode_json(payload)) < len(payload.encode("utf-8"))
