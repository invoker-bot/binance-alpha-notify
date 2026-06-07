from pathlib import Path

import alpha_notify.paths as paths


def test_db_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPHA_NOTIFY_DB_PATH", str(tmp_path / "x.db"))
    assert paths.get_db_file() == tmp_path / "x.db"


def test_cache_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPHA_NOTIFY_CACHE_PATH", str(tmp_path / "x.json"))
    assert paths.get_cache_file() == tmp_path / "x.json"


def test_config_dir_created(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.platformdirs, "user_config_dir",
                        lambda app, appauthor=None: str(tmp_path / "cfg" / app))
    d = paths.get_config_dir()
    assert d.exists()
    assert d == tmp_path / "cfg" / "alpha-notify"


def test_db_default(monkeypatch, tmp_path):
    monkeypatch.delenv("ALPHA_NOTIFY_DB_PATH", raising=False)
    monkeypatch.setattr(paths.platformdirs, "user_data_dir",
                        lambda app, appauthor=None: str(tmp_path / "data" / app))
    assert paths.get_db_file() == tmp_path / "data" / "alpha-notify" / "notifications.db"


def test_db_override_expands_tilde(monkeypatch):
    monkeypatch.setenv("ALPHA_NOTIFY_DB_PATH", "~/x.db")
    assert paths.get_db_file() == Path("~/x.db").expanduser()


def test_cache_override_expands_tilde(monkeypatch):
    monkeypatch.setenv("ALPHA_NOTIFY_CACHE_PATH", "~/c.json")
    assert paths.get_cache_file() == Path("~/c.json").expanduser()
