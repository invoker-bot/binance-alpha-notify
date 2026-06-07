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


def _normalized_for_compare(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """归一化用于比较：移除注入的行情字段(price/dex_price)，并按稳定顺序排序，
    使变化检测不受价格富集差异和列表顺序影响。"""
    projected = [
        {k: v for k, v in item.items() if k not in ("price", "dex_price")}
        for item in records
        if isinstance(item, dict)
    ]
    projected.sort(key=lambda r: json.dumps(r, sort_keys=True, ensure_ascii=False))
    return projected


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
    current_payload = json.dumps(_normalized_for_compare(today), sort_keys=True, ensure_ascii=False)
    cached_payload = json.dumps(_normalized_for_compare(old_today), sort_keys=True, ensure_ascii=False)
    if current_payload != cached_payload:
        return True, "🔄 检测到当天空投变化，将发送通知。"
    return False, "✅ 当天空投无变化，无需通知。"
