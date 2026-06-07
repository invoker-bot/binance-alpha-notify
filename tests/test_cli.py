import alpha_notify.cli as cli
from alpha_notify.config import Config


def _patch_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "get_config_file", lambda: tmp_path / "config.ini")
    monkeypatch.setattr(cli, "get_data_dir", lambda: tmp_path)
    monkeypatch.setattr(cli, "get_db_file", lambda: tmp_path / "n.db")
    monkeypatch.setattr(cli, "get_cache_file", lambda: tmp_path / "c.json")


def test_config_path(monkeypatch, tmp_path, capsys):
    _patch_paths(monkeypatch, tmp_path)
    assert cli.main(["config", "path"]) == 0
    assert "配置文件" in capsys.readouterr().out


def test_config_init_creates(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    assert cli.main(["config", "init"]) == 0
    assert (tmp_path / "config.ini").exists()


def test_run_no_urls_returns_error(monkeypatch, tmp_path, capsys):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda p: Config(apprise_urls=[]))
    assert cli.main(["run"]) == 1
    assert "APPRISE_URLS" in capsys.readouterr().out


def test_run_dry_run_invokes_core(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda p: Config(apprise_urls=[]))
    monkeypatch.setattr(cli, "AlphaClient", lambda **kw: object())
    captured = {}

    def fake_check(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(cli, "check_for_updates", fake_check)
    assert cli.main(["run", "--dry-run"]) == 0
    assert captured["dry_run"] is True


def test_default_command_is_run(monkeypatch):
    called = {}
    monkeypatch.setattr(cli, "cmd_run", lambda ns: called.setdefault("ran", True) or 0)
    assert cli.main([]) == 0
    assert called.get("ran")
