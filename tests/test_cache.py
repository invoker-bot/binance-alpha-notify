from alpha_notify.cache import detect_changes, load_cached_data, save_cached_data


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
