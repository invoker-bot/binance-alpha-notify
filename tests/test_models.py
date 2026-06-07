from datetime import datetime, timedelta, timezone

from alpha_notify.models import (
    Airdrop,
    format_airdrop_message,
    is_precise_time,
    select_today_airdrops,
)

BJ = timezone(timedelta(hours=8))
NOW = datetime(2026, 6, 8, 10, 0, 0, tzinfo=BJ)


def test_is_precise_time():
    assert is_precise_time("15:00")
    assert is_precise_time("9:05:30")
    assert not is_precise_time("待定")
    assert not is_precise_time("")


def test_from_record_future_today():
    record = {"id": "a1", "token": "FOO", "date": "2026-06-08", "time": "15:00",
              "amount": "100", "points": "200"}
    prices = {"FOO": {"price": "2.5", "dex_price": "2.4"}}
    drop = Airdrop.from_record(record, prices, NOW)
    assert drop is not None
    assert drop.identity == "a1"
    assert drop.token == "FOO"
    assert drop.price == 2.5
    assert drop.total_value == 250.0
    assert drop.formatted_value == "250.00"


def test_from_record_past_is_skipped():
    record = {"id": "a2", "token": "BAR", "date": "2026-06-08", "time": "09:00",
              "amount": "1", "points": "1"}
    assert Airdrop.from_record(record, {}, NOW) is None


def test_from_record_other_day_skipped():
    record = {"id": "a3", "token": "BAZ", "date": "2026-06-09", "time": "15:00"}
    assert Airdrop.from_record(record, {}, NOW) is None


def test_select_today_counts_skipped_without_time():
    records = [
        {"id": "1", "token": "A", "date": "2026-06-08", "time": "15:00"},
        {"id": "2", "token": "B", "date": "2026-06-08", "time": "待定"},
        {"id": "3", "token": "C", "date": "2026-06-07", "time": "15:00"},
    ]
    raw, parsed, skipped = select_today_airdrops(records, {}, NOW)
    assert [p.identity for p in parsed] == ["1"]
    assert len(raw) == 1
    assert skipped == 1


def test_select_today_dedups_identity():
    records = [
        {"id": "dup", "token": "A", "date": "2026-06-08", "time": "15:00"},
        {"id": "dup", "token": "A", "date": "2026-06-08", "time": "15:00"},
    ]
    _, parsed, _ = select_today_airdrops(records, {}, NOW)
    assert len(parsed) == 1


def test_select_today_skips_non_dict_records():
    records = [
        "garbage",
        {"id": "1", "token": "A", "date": "2026-06-08", "time": "15:00"},
        123,
    ]
    raw, parsed, _ = select_today_airdrops(records, {}, NOW)
    assert [p.identity for p in parsed] == ["1"]
    assert len(raw) == 1


def test_format_message():
    drop = Airdrop.from_record(
        {"id": "x", "token": "FOO", "date": "2026-06-08", "time": "15:00",
         "amount": "100", "points": "200"},
        {"FOO": {"price": "2.5"}},
        NOW,
    )
    msg = format_airdrop_message([drop])
    assert "共 1 条" in msg
    assert "空投名称：FOO" in msg
    assert "$250.00" in msg
