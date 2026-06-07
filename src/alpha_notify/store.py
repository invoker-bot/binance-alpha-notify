from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from .errors import AlphaNotifyError
from .models import Airdrop


class NotificationStore:
    """记录通知发送状态的本地存储 (SQLite)"""

    def __init__(self, path: Path):
        self.path = path
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # 目录创建失败时交由后续数据库连接报错
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def _ensure_schema(self) -> None:
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notifications (
                        identity TEXT PRIMARY KEY,
                        date TEXT NOT NULL,
                        token TEXT NOT NULL,
                        time TEXT NOT NULL,
                        sent_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_notifications_date ON notifications(date)"
                )
        except sqlite3.Error as exc:
            raise AlphaNotifyError(f"初始化通知数据库失败: {exc}") from exc

    def cleanup(self, current_date: str) -> None:
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute("DELETE FROM notifications WHERE date <> ?", (current_date,))
        except sqlite3.Error as exc:
            raise AlphaNotifyError(f"清理通知数据库失败: {exc}") from exc

    def filter_unsent(self, airdrops: Sequence[Airdrop]) -> List[Airdrop]:
        if not airdrops:
            return []
        identities = [item.identity for item in airdrops]
        placeholders = ",".join("?" for _ in identities)
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute(
                    f"SELECT identity FROM notifications WHERE identity IN ({placeholders})",
                    identities,
                ).fetchall()
        except sqlite3.Error as exc:
            raise AlphaNotifyError(f"查询通知数据库失败: {exc}") from exc
        delivered = {row[0] for row in rows}
        return [item for item in airdrops if item.identity not in delivered]

    def mark_sent(self, airdrops: Sequence[Airdrop], sent_at: datetime) -> None:
        if not airdrops:
            return
        payload = [
            (item.identity, item.date, item.token, item.time, sent_at.isoformat(timespec="seconds"))
            for item in airdrops
        ]
        try:
            with closing(self._connect()) as conn, conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO notifications (identity, date, token, time, sent_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    payload,
                )
        except sqlite3.Error as exc:
            raise AlphaNotifyError(f"写入通知数据库失败: {exc}") from exc
