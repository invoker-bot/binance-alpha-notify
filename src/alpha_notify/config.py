from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .errors import AlphaNotifyError
from .paths import get_config_file

CONFIG_SECTION = "alpha-notify"

CONFIG_TEMPLATE = """\
[alpha-notify]
# Apprise 通知配置：每行一个 URL，或单行用逗号分隔。
# 注意：若某个 URL 本身包含逗号（如 mailto 的多个收件人 ?to=a,b），请让它单独成行。
# 完整服务列表与格式：https://github.com/caronc/apprise
#
# 示例：
#   飞书:     lark://WEBHOOK
#   钉钉:     dingtalk://ACCESS_TOKEN
#   Telegram: tgram://BOT_TOKEN/CHAT_ID
#   Bark:     bark://DEVICE_KEY@HOST
#   邮件:     mailto://user:pass@example.com
apprise_urls =

# HTTP 请求超时（秒）
timeout = 30

# 时区小时偏移（北京时间为 8）
timezone = 8
"""


@dataclass
class Config:
    apprise_urls: List[str] = field(default_factory=list)
    timeout: int = 30
    timezone_offset: int = 8


def _split_urls(raw: str) -> List[str]:
    # 多个 URL 可每行一个（含逗号的 URL 应单独成行）；
    # 单行时回退到逗号分隔，兼容旧配置与环境变量写法。
    if "\n" in raw or "\r" in raw:
        parts = raw.splitlines()
    else:
        parts = raw.split(",")
    return [p.strip() for p in parts if p.strip()]


def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置：APPRISE_URLS 环境变量 > 配置文件"""
    path = config_path if config_path is not None else get_config_file()
    if config_path is not None and not path.is_file():
        raise AlphaNotifyError(f"配置文件不存在: {path}")

    apprise_urls: List[str] = []
    timeout = 30
    timezone_offset = 8

    if path.is_file():
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read(path, encoding="utf-8-sig")
        except (configparser.Error, OSError) as exc:
            raise AlphaNotifyError(f"读取配置文件失败: {exc}") from exc
        if parser.has_section(CONFIG_SECTION):
            section = parser[CONFIG_SECTION]
            apprise_urls = _split_urls(section.get("apprise_urls", ""))
            try:
                timeout = section.getint("timeout", fallback=30)
                timezone_offset = section.getint("timezone", fallback=8)
            except ValueError as exc:
                raise AlphaNotifyError(f"配置文件数值字段无效: {exc}") from exc

    env_urls = os.getenv("APPRISE_URLS")
    if env_urls is not None and env_urls.strip():
        apprise_urls = _split_urls(env_urls)

    if not -23 <= timezone_offset <= 23:
        raise AlphaNotifyError(
            f"配置项 timezone 超出范围（应在 -23 到 23 之间）: {timezone_offset}"
        )

    return Config(apprise_urls=apprise_urls, timeout=timeout, timezone_offset=timezone_offset)


def write_template_config(path: Path) -> None:
    """写入配置模板"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    except OSError as exc:
        raise AlphaNotifyError(f"写入配置模板失败: {exc}") from exc


def mask_urls(urls: List[str]) -> List[str]:
    """对 URL 中的敏感部分脱敏"""
    masked = []
    for url in urls:
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if len(rest) <= 4:
                masked.append(f"{scheme}://***")
            else:
                masked.append(f"{scheme}://{rest[:2]}***{rest[-2:]}")
        else:
            masked.append("***")
    return masked
