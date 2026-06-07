from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, tzinfo
from typing import Any, Dict, List, Optional, Sequence, Tuple

DATETIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


def is_precise_time(value: str) -> bool:
    """判断时间字符串是否为具体时间 (HH:MM[:SS])"""
    return bool(TIME_PATTERN.match(value.strip()))


def _parse_datetime(date_str: str, time_str: str, tz: tzinfo) -> Optional[datetime]:
    """以多种格式解析日期时间，并附加时区"""
    combined = f"{date_str.strip()} {time_str.strip()}"
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(combined, fmt).replace(tzinfo=tz)
        except ValueError:
            continue
    return None


def _as_float(value: Any) -> Optional[float]:
    """尝试将值转换为浮点数"""
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


@dataclass(frozen=True)
class Airdrop:
    identity: str
    token: str
    date: str
    time: str
    amount: str
    points: str
    price: Optional[float]
    dex_price: Optional[float]
    scheduled_at: datetime

    @classmethod
    def from_record(
        cls,
        record: Dict[str, Any],
        prices: Dict[str, Dict[str, Any]],
        now: datetime,
    ) -> Optional["Airdrop"]:
        date_raw = record.get("date")
        time_raw = record.get("time")
        if not date_raw or not time_raw:
            return None

        date_str = str(date_raw)
        time_str = str(time_raw)

        if now.tzinfo is None:
            return None

        scheduled = _parse_datetime(date_str, time_str, now.tzinfo)
        if scheduled is None or scheduled.date() != now.date() or scheduled <= now:
            return None

        token_raw = record.get("token")
        token = str(token_raw).strip() if token_raw else "(无名)"

        token_key = record.get("token", "")
        price_info = prices.get(token_key, {})
        if not isinstance(price_info, dict):
            price_info = {}

        identity_raw = record.get("id")
        identity = str(identity_raw) if identity_raw else f"{token}|{date_str}|{time_str}"

        amount_raw = record.get("amount") or "未知"
        points_raw = record.get("points") or "未知"

        return cls(
            identity=identity,
            token=token,
            date=date_str,
            time=time_str,
            amount=str(amount_raw),
            points=str(points_raw),
            price=_as_float(price_info.get("price")),
            dex_price=_as_float(price_info.get("dex_price")),
            scheduled_at=scheduled,
        )

    @property
    def total_value(self) -> Optional[float]:
        amount_value = _as_float(self.amount)
        if amount_value is None or self.price is None:
            return None
        return self.price * amount_value

    @property
    def formatted_value(self) -> str:
        total = self.total_value
        return f"{total:.2f}" if total is not None else "未知"


def select_today_airdrops(
    records: List[Dict[str, Any]],
    prices: Dict[str, Dict[str, Any]],
    now: datetime,
) -> Tuple[List[Dict[str, Any]], List[Airdrop], int]:
    """筛选今天未到期的空投，返回 (原始数据, 解析结果, 缺时间跳过计数)"""
    today_raw_map: Dict[str, Dict[str, Any]] = {}
    parsed_map: Dict[str, Airdrop] = {}
    skipped_without_time = 0
    today_str = now.strftime("%Y-%m-%d")

    for record in records:
        if not isinstance(record, dict):
            continue
        date_value = record.get("date")
        if not date_value or str(date_value) != today_str:
            continue

        time_value = record.get("time")
        if not time_value or not is_precise_time(str(time_value)):
            skipped_without_time += 1
            continue

        airdrop = Airdrop.from_record(record, prices, now)
        if not airdrop:
            continue
        if airdrop.identity in parsed_map:
            continue

        price_info = prices.get(record.get("token", ""), {})
        enriched = dict(record)
        if isinstance(price_info, dict):
            enriched["price"] = price_info.get("price")
            enriched["dex_price"] = price_info.get("dex_price")
        else:
            enriched["price"] = None
            enriched["dex_price"] = None

        today_raw_map[airdrop.identity] = enriched
        parsed_map[airdrop.identity] = airdrop

    return list(today_raw_map.values()), list(parsed_map.values()), skipped_without_time


def format_airdrop_message(airdrops: Sequence[Airdrop]) -> str:
    """将空投列表格式化为多行文本"""
    detail_blocks = []
    for item in airdrops:
        detail_blocks.append(
            "\n".join(
                (
                    f"空投名称：{item.token}",
                    f"空投时间：{item.date} {item.time}",
                    f"空投数量：{item.amount}",
                    f"所需积分：{item.points}",
                    f"空投金额：${item.formatted_value}",
                )
            )
        )
    header = f"🔔 检测到今天的新空投，共 {len(airdrops)} 条"
    return f"{header}\n\n" + "\n\n".join(detail_blocks)
