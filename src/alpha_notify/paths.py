from __future__ import annotations

import os
from pathlib import Path

import platformdirs

APP_NAME = "alpha-notify"


def get_config_dir() -> Path:
    # appauthor=False 避免 Windows 上出现 alpha-notify\alpha-notify 的重复目录层级
    path = Path(platformdirs.user_config_dir(APP_NAME, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    path = Path(platformdirs.user_data_dir(APP_NAME, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file() -> Path:
    return get_config_dir() / "config.ini"


def get_db_file() -> Path:
    override = os.getenv("ALPHA_NOTIFY_DB_PATH")
    if override:
        return Path(override).expanduser()
    return get_data_dir() / "notifications.db"


def get_cache_file() -> Path:
    override = os.getenv("ALPHA_NOTIFY_CACHE_PATH")
    if override:
        return Path(override).expanduser()
    return get_data_dir() / "airdrop_data.json"
