from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

from .errors import AlphaNotifyError

DATA_URL = "https://alpha123.uk/api/data?fresh=1"
PRICE_URL = "https://alpha123.uk/api/price/?batch=today"

HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "referer": "https://alpha123.uk/zh/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
}


class AlphaClient:
    """alpha123.uk API 客户端"""

    def __init__(self, timeout: int = 30, session: Optional[requests.Session] = None):
        self.timeout = timeout
        self.session = session or requests.Session()

    def _fetch_json(self, url: str, description: str) -> Any:
        try:
            response = self.session.get(url, headers=HEADERS, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise AlphaNotifyError(f"请求{description}失败: {exc}") from exc
        except ValueError as exc:
            raise AlphaNotifyError(f"解析{description}失败: {exc}") from exc

    def fetch_airdrops(self) -> List[Dict[str, Any]]:
        data = self._fetch_json(DATA_URL, "空投数据")
        if isinstance(data, dict):
            data = data.get("airdrops", data)
        if not isinstance(data, list):
            snippet = json.dumps(data, ensure_ascii=False)[:200]
            raise AlphaNotifyError(f"数据格式异常: {snippet}")
        return data

    def fetch_prices(self) -> Dict[str, Dict[str, Any]]:
        data = self._fetch_json(PRICE_URL, "价格数据")
        if isinstance(data, dict):
            prices = data.get("prices")
            if isinstance(prices, dict):
                return prices
        return {}
