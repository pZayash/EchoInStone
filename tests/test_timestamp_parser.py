import pytest

from EchoInStone.processing.timestamp_parser import parse_timestamp, parse_timestamp_list


def test_parse_timestamp_seconds_float():
    assert parse_timestamp("123.5") == 123.5


def test_parse_timestamp_mm_ss():
    assert parse_timestamp("5:30") == 330.0


def test_parse_timestamp_hh_mm_ss():
    assert parse_timestamp("1:02:03") == 3723.0


def test_parse_timestamp_invalid():
    with pytest.raises(ValueError):
        parse_timestamp("bad")


def test_parse_timestamp_list():
    assert parse_timestamp_list("1:00, 90, 0:30") == [30.0, 60.0, 90.0]
