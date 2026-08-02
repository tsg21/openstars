"""Unit tests for openstars.server.log_context."""

import logging

from openstars.server.log_context import game_id, log_duration, turn
from openstars.server.logging import ContextFilter


def test_log_duration_logs_elapsed_time(caplog):
    log = logging.getLogger("test_log_duration")
    with caplog.at_level(logging.INFO, logger="test_log_duration"):
        with log_duration(log, "my_phase"):
            pass

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert message.startswith("my_phase done in")
    assert message.endswith("ms")


def test_log_duration_logs_even_on_exception(caplog):
    log = logging.getLogger("test_log_duration_exc")
    with caplog.at_level(logging.INFO, logger="test_log_duration_exc"):
        try:
            with log_duration(log, "failing_phase"):
                raise ValueError("boom")
        except ValueError:
            pass

    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage().startswith("failing_phase done in")


def test_context_filter_attaches_game_id_and_turn():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    filt = ContextFilter()

    token_g = game_id.set("game-1")
    token_t = turn.set(3)
    try:
        assert filt.filter(record) is True
        assert record.game_id == "game-1"
        assert record.turn == 3
    finally:
        game_id.reset(token_g)
        turn.reset(token_t)


def test_context_filter_leaves_record_unset_when_no_context():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    filt = ContextFilter()

    assert filt.filter(record) is True
    assert not hasattr(record, "game_id")
    assert not hasattr(record, "turn")
