from __future__ import annotations

from typing import List

import apprise

from .errors import AlphaNotifyError


class Notifier:
    """基于 Apprise 的通知发送器"""

    def __init__(self, urls: List[str]):
        self.urls = urls

    def send(self, title: str, body: str) -> int:
        """发送通知，返回成功配置的服务数量"""
        if not self.urls:
            raise AlphaNotifyError("未配置 APPRISE_URLS，无法发送通知")

        asset = apprise.AppriseAsset(app_id="空投助手")
        notifier = apprise.Apprise(asset=asset)
        for url in self.urls:
            notifier.add(url)

        if len(notifier) == 0:
            raise AlphaNotifyError("没有有效的通知服务配置")

        try:
            success = notifier.notify(title=title, body=body)
        except Exception as exc:  # noqa: BLE001 - Apprise 未提供更精确的异常基类
            raise AlphaNotifyError("通知发送失败") from exc

        if not success:
            raise AlphaNotifyError("通知发送失败")

        return len(notifier)
