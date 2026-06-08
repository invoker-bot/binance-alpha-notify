from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import cache as cache_mod
from .client import AlphaClient
from .errors import AlphaNotifyError
from .models import format_airdrop_message, format_airdrop_title, select_today_airdrops
from .notifier import Notifier
from .store import NotificationStore


def _tz_label(now: datetime) -> str:
    offset = now.utcoffset()
    if offset is None:
        return "本地"
    hours = int(offset.total_seconds() // 3600)
    return f"UTC{hours:+d}"


def check_for_updates(
    *,
    client: AlphaClient,
    store: Optional[NotificationStore],
    notifier: Optional[Notifier],
    cache_path: Path,
    now: datetime,
    debug: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> str:
    """检查空投更新并返回逐行日志文本。外部依赖均由参数注入。"""
    today_str = now.strftime("%Y-%m-%d")
    log: List[str] = [f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} ({_tz_label(now)})"]

    try:
        data = client.fetch_airdrops()
        log.append(f"📦 当前获取 {len(data)} 条记录")
    except AlphaNotifyError as exc:
        log.append(f"❌ {exc}")
        return "\n".join(log)

    try:
        prices = client.fetch_prices()
    except AlphaNotifyError as exc:
        log.append(f"⚠️ {exc}")
        prices = {}

    today_raw, today_airdrops, skipped_no_time = select_today_airdrops(data, prices, now)
    if skipped_no_time:
        log.append(f"ℹ️ 有 {skipped_no_time} 条空投缺少具体领取时间，已跳过。")

    if not today_airdrops:
        log.append("⚠️ 当前没有可发送的空投，跳过通知。")
        return "\n".join(log)

    try:
        cached_data = cache_mod.load_cached_data(cache_path)
    except AlphaNotifyError as exc:
        log.append(f"⚠️ {exc}")
        cached_data = None

    changed, status = cache_mod.detect_changes(cached_data, today_raw, today_str)
    log.append(status)

    pending_airdrops = list(today_airdrops)
    if store is not None:
        try:
            store.cleanup(today_str)
        except AlphaNotifyError as exc:
            log.append(f"⚠️ 清理历史记录失败，将继续去重: {exc}")

    if store is not None and not force:
        try:
            pending_airdrops = store.filter_unsent(today_airdrops)
            skipped = len(today_airdrops) - len(pending_airdrops)
            if skipped:
                log.append(f"ℹ️ 已推送 {skipped} 条记录，将跳过。")
        except AlphaNotifyError as exc:
            log.append(f"⚠️ {exc}")
            pending_airdrops = list(today_airdrops)

    if not pending_airdrops:
        log.append("✅ 当前待推送列表为空（已推送或需等待领取时间）。")
        return "\n".join(log)

    if changed and not dry_run:
        try:
            cache_mod.save_cached_data(cache_path, data)
        except AlphaNotifyError as exc:
            log.append(f"⚠️ {exc}")

    message = format_airdrop_message(pending_airdrops)
    title = format_airdrop_title(pending_airdrops)

    if debug or dry_run:
        log.append("\n--- 通知内容预览 ---")
        log.append(f"标题: {title}")
        log.append(message)
        log.append("--- 预览结束 ---")

    if dry_run:
        log.append("🛈 dry-run 模式，未发送通知、未写入数据库。")
        return "\n".join(log)

    if notifier is None:
        log.append("⚠️ 未配置 APPRISE_URLS，跳过通知发送。")
        return "\n".join(log)

    try:
        count = notifier.send(title, message)
        log.append(f"✅ 通知已发送到 {count} 个服务")
        if store is not None and not force:
            try:
                store.mark_sent(pending_airdrops, now)
            except AlphaNotifyError as exc:
                log.append(f"⚠️ {exc}")
    except AlphaNotifyError as exc:
        log.append(f"❌ {exc}")

    return "\n".join(log)
