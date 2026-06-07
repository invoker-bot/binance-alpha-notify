import pytest

from datetime import datetime, timedelta, timezone

from alpha_notify.cache import detect_changes, load_cached_data, save_cached_data
from alpha_notify.errors import AlphaNotifyError
from alpha_notify.models import select_today_airdrops

BJ = timezone(timedelta(hours=8))
NOW = datetime(2026, 6, 8, 10, 0, 0, tzinfo=BJ)


def test_load_missing_returns_none(tmp_path):
    assert load_cached_data(tmp_path / "missing.json") is None


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "c.json"
    data = [{"id": "1", "date": "2026-06-08", "time": "15:00"}]
    save_cached_data(path, data)
    assert load_cached_data(path) == data


def test_detect_changes_first_time():
    changed, msg = detect_changes(None, [{"a": 1}], "2026-06-08")
    assert changed is True
    assert msg


def test_detect_changes_no_change():
    today = [{"date": "2026-06-08", "time": "15:00", "token": "A"}]
    cached = [{"date": "2026-06-08", "time": "15:00", "token": "A"}]
    changed, _ = detect_changes(cached, today, "2026-06-08")
    assert changed is False


def test_detect_changes_changed():
    today = [{"date": "2026-06-08", "time": "16:00", "token": "A"}]
    cached = [{"date": "2026-06-08", "time": "15:00", "token": "A"}]
    changed, _ = detect_changes(cached, today, "2026-06-08")
    assert changed is True


def test_detect_changes_stable_across_runs_with_enriched_today(tmp_path):
    # Mirrors the real core flow: enriched today_raw vs cached full raw data.
    data = [
        {"id": "1", "token": "FOO", "date": "2026-06-08", "time": "15:00",
         "amount": "100", "points": "200"},
        {"id": "2", "token": "BAR", "date": "2026-06-07", "time": "15:00"},
        {"id": "3", "token": "BAZ", "date": "2026-06-08", "time": "待定"},
    ]
    prices = {"FOO": {"price": "2.5", "dex_price": "2.4"}}
    path = tmp_path / "c.json"
    save_cached_data(path, data)  # core saves the FULL raw data
    cached = load_cached_data(path)
    today_raw, _, _ = select_today_airdrops(data, prices, NOW)  # enriched
    changed, _ = detect_changes(cached, today_raw, "2026-06-08")
    assert changed is False


def test_detect_changes_ignores_list_order():
    base = [
        {"id": "1", "token": "A", "date": "2026-06-08", "time": "15:00"},
        {"id": "2", "token": "B", "date": "2026-06-08", "time": "16:00"},
    ]
    changed, _ = detect_changes(list(reversed(base)), base, "2026-06-08")
    assert changed is False


def test_load_empty_file_returns_empty(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    assert load_cached_data(path) == []


def test_load_non_list_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(AlphaNotifyError):
        load_cached_data(path)
