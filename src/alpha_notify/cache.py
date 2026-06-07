from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .errors import AlphaNotifyError
from .models import is_precise_time


def load_cached_data(path: Path) -> Optional[List[Dict[str, Any]]]:
    """从文件加载缓存数据；不存在返回 None"""
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return []
        data = json.loads(content)
        if not isinstance(data, list):
            raise AlphaNotifyError("缓存数据格式异常")
        return data
    except (OSError, json.JSONDecodeError) as exc:
        raise AlphaNotifyError(f"读取缓存数据失败: {exc}") from exc


def save_cached_data(path: Path, data: List[Dict[str, Any]]) -> None:
    """将数据写入缓存文件"""
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise AlphaNotifyError(f"保存缓存数据失败: {exc}") from exc


def detect_changes(
    cached: Optional[List[Dict[str, Any]]],
    today: List[Dict[str, Any]],
    today_str: str,
) -> Tuple[bool, str]:
    """判断当天空投相对缓存是否有变化"""
    if cached is None:
        return True, "💾 无历史数据，首次保存。"
    old_today = [
        item
        for item in cached
        if isinstance(item, dict)
        and item.get("date") == today_str
        and item.get("time")
        and is_precise_time(str(item.get("time")))
    ]
    current_payload = json.dumps(today, sort_keys=True, ensure_ascii=False)
    cached_payload = json.dumps(old_today, sort_keys=True, ensure_ascii=False)
    if current_payload != cached_payload:
        return True, "🔄 检测到当天空投变化，将发送通知。"
    return False, "✅ 当天空投无变化，无需通知。"
