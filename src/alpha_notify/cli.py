from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .client import AlphaClient
from .config import Config, load_config, mask_urls, write_template_config
from .core import check_for_updates
from .errors import AlphaNotifyError
from .notifier import Notifier
from .paths import get_cache_file, get_config_file, get_data_dir, get_db_file
from .store import NotificationStore


def _configure_stdout() -> None:
    """尽量让标准输出使用 UTF-8，避免 Windows 控制台 emoji 报错。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alpha-notify", description="Binance Alpha 空投通知 CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    # 无子命令时默认执行 run（使用默认参数）。
    parser.set_defaults(func=cmd_run, test=False, debug=False, dry_run=False, config=None)
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="抓取并推送空投通知（默认命令）")
    run.add_argument("-t", "--test", action="store_true", help="强制发送（忽略去重）")
    run.add_argument("-d", "--debug", action="store_true", help="详细日志 + 异常 traceback")
    run.add_argument("--dry-run", action="store_true", help="只预览不发送、不写库")
    run.add_argument("--config", type=Path, default=None, help="指定配置文件路径")
    run.set_defaults(func=cmd_run)

    config = sub.add_parser("config", help="配置管理")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    c_init = config_sub.add_parser("init", help="生成配置模板")
    c_init.set_defaults(func=cmd_config_init)

    c_path = config_sub.add_parser("path", help="打印配置/数据路径")
    c_path.set_defaults(func=cmd_config_path)

    c_show = config_sub.add_parser("show", help="打印生效配置（脱敏）")
    c_show.add_argument("--config", type=Path, default=None, help="指定配置文件路径")
    c_show.set_defaults(func=cmd_config_show)

    return parser


def _build_now(config: Config) -> datetime:
    tz = timezone(timedelta(hours=config.timezone_offset))
    return datetime.now(tz)


def cmd_run(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except AlphaNotifyError as exc:
        print(f"❌ {exc}")
        return 1

    if not config.apprise_urls and not args.dry_run:
        print("⚠️ 未配置 APPRISE_URLS。请运行 `alpha-notify config init` 生成配置，"
              "或设置环境变量 APPRISE_URLS。")
        return 1

    now = _build_now(config)
    client = AlphaClient(timeout=config.timeout)

    store: Optional[NotificationStore] = None
    if not args.dry_run:
        try:
            store = NotificationStore(get_db_file())
        except AlphaNotifyError as exc:
            print(f"⚠️ {exc}")
            store = None

    notifier: Optional[Notifier] = Notifier(config.apprise_urls) if config.apprise_urls else None

    try:
        result = check_for_updates(
            client=client,
            store=store,
            notifier=notifier,
            cache_path=get_cache_file(),
            now=now,
            debug=args.debug,
            force=args.test,
            dry_run=args.dry_run,
        )
        print(result)
        return 0
    except AlphaNotifyError as exc:
        print(f"❌ 程序执行失败: {exc}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def cmd_config_init(args: argparse.Namespace) -> int:
    path = get_config_file()
    if path.exists():
        print(f"配置文件已存在：{path}")
        return 0
    try:
        write_template_config(path)
    except AlphaNotifyError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"已生成配置模板：{path}")
    print("请编辑该文件，填入 apprise_urls。")
    return 0


def cmd_config_path(args: argparse.Namespace) -> int:
    print(f"配置文件：{get_config_file()}")
    print(f"数据目录：{get_data_dir()}")
    print(f"去重数据库：{get_db_file()}")
    print(f"缓存文件：{get_cache_file()}")
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except AlphaNotifyError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"timeout = {config.timeout}")
    print(f"timezone = {config.timezone_offset}")
    urls = mask_urls(config.apprise_urls)
    if urls:
        print("apprise_urls:")
        for url in urls:
            print(f"  - {url}")
    else:
        print("apprise_urls: (未配置)")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    # 顶层 set_defaults(func=cmd_run) 保证无子命令时回退到 run。
    return args.func(args)
