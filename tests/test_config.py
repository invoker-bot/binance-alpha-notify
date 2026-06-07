import pytest

from alpha_notify.config import load_config, mask_urls, write_template_config
from alpha_notify.errors import AlphaNotifyError


def test_load_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("APPRISE_URLS", raising=False)
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(
        "[alpha-notify]\napprise_urls = a://x, b://y\ntimeout = 15\ntimezone = 0\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.apprise_urls == ["a://x", "b://y"]
    assert cfg.timeout == 15
    assert cfg.timezone_offset == 0


def test_env_overrides_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text("[alpha-notify]\napprise_urls = file://only\n", encoding="utf-8")
    monkeypatch.setenv("APPRISE_URLS", "env://one, env://two")
    cfg = load_config(cfg_file)
    assert cfg.apprise_urls == ["env://one", "env://two"]


def test_missing_file_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("APPRISE_URLS", raising=False)
    cfg = load_config(tmp_path / "nope.ini")
    assert cfg.apprise_urls == []
    assert cfg.timeout == 30
    assert cfg.timezone_offset == 8


def test_url_with_percent_is_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv("APPRISE_URLS", raising=False)
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text("[alpha-notify]\napprise_urls = sch://a%20b\n", encoding="utf-8")
    cfg = load_config(cfg_file)
    assert cfg.apprise_urls == ["sch://a%20b"]


def test_write_template(tmp_path):
    path = tmp_path / "sub" / "config.ini"
    write_template_config(path)
    assert path.exists()
    assert "[alpha-notify]" in path.read_text(encoding="utf-8")


def test_mask_urls():
    masked = mask_urls(["tgram://123456789:ABCdef"])
    assert masked[0].startswith("tgram://")
    assert "***" in masked[0]
    assert "123456789" not in masked[0]


def test_out_of_range_timezone_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("APPRISE_URLS", raising=False)
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text("[alpha-notify]\ntimezone = 999\n", encoding="utf-8")
    with pytest.raises(AlphaNotifyError):
        load_config(cfg_file)
