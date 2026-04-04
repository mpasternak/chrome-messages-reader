"""Tests for chrome_messages_reader.parsers — all data is synthetic."""

from chrome_messages_reader.parsers import parse_pzepuap_messages


def test_auth_code_single():
    texts = ["Kod autoryzacyjny nr 1 z 01.01.2025: 12345678"]
    result = parse_pzepuap_messages(texts)
    assert result == [
        {"type": "auth_code", "number": "1", "date": "01.01.2025", "code": "12345678"},
    ]


def test_auth_code_multiple():
    texts = [
        "Kod autoryzacyjny nr 1 z 15.06.2025: 11111111",
        "Kod autoryzacyjny nr 2 z 15.06.2025: 22222222",
        "Kod autoryzacyjny nr 3 z 15.06.2025: 33333333",
    ]
    result = parse_pzepuap_messages(texts)
    assert len(result) == 3
    assert result[0]["number"] == "1"
    assert result[1]["number"] == "2"
    assert result[2]["code"] == "33333333"


def test_signing_code():
    texts = ["Podpisanie dokumentu: 01.01.2025, godz. 10:30:00. Kod: 99887766"]
    result = parse_pzepuap_messages(texts)
    assert result == [
        {"type": "signing_code", "date": "01.01.2025", "time": "10:30:00", "code": "99887766"},
    ]


def test_signing_code_without_dot_after_godz():
    texts = ["Podpisanie dokumentu: 02.02.2025, godz 14:00:00. Kod: 55566677"]
    result = parse_pzepuap_messages(texts)
    assert len(result) == 1
    assert result[0]["type"] == "signing_code"
    assert result[0]["time"] == "14:00:00"


def test_mixed_messages():
    texts = [
        "Kod autoryzacyjny nr 1 z 10.03.2025: 11112222",
        "Hello, this is an unrelated message",
        "Podpisanie dokumentu: 10.03.2025, godz. 09:15:30. Kod: 33334444",
        "Another random SMS text",
        "Kod autoryzacyjny nr 2 z 10.03.2025: 55556666",
    ]
    result = parse_pzepuap_messages(texts)
    assert len(result) == 3
    assert result[0]["type"] == "auth_code"
    assert result[1]["type"] == "signing_code"
    assert result[2]["type"] == "auth_code"
    assert result[2]["number"] == "2"


def test_unrelated_messages_skipped():
    texts = [
        "Twoja paczka zostala nadana",
        "Reminder: spotkanie o 15:00",
        "",
    ]
    result = parse_pzepuap_messages(texts)
    assert result == []


def test_empty_input():
    assert parse_pzepuap_messages([]) == []


def test_extra_whitespace_in_auth_code():
    texts = ["Kod autoryzacyjny nr  42  z  01.01.2025:  87654321"]
    result = parse_pzepuap_messages(texts)
    assert len(result) == 1
    assert result[0]["number"] == "42"
    assert result[0]["code"] == "87654321"


def test_signing_code_date_whitespace_stripped():
    texts = ["Podpisanie dokumentu:  20.05.2025, godz. 12:00:00. Kod: 11223344"]
    result = parse_pzepuap_messages(texts)
    assert result[0]["date"] == "20.05.2025"
