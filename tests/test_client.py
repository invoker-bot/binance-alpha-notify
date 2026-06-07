import pytest

from alpha_notify.client import HEADERS, AlphaClient
from alpha_notify.errors import AlphaNotifyError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, headers, timeout))
        return FakeResponse(self._payload)


def test_fetch_airdrops_list():
    client = AlphaClient(session=FakeSession([{"id": "1"}]))
    assert client.fetch_airdrops() == [{"id": "1"}]


def test_fetch_airdrops_wrapped():
    client = AlphaClient(session=FakeSession({"airdrops": [{"id": "2"}]}))
    assert client.fetch_airdrops() == [{"id": "2"}]


def test_fetch_airdrops_bad_format_raises():
    client = AlphaClient(session=FakeSession(12345))
    with pytest.raises(AlphaNotifyError):
        client.fetch_airdrops()


def test_fetch_prices_returns_prices():
    client = AlphaClient(session=FakeSession({"prices": {"FOO": {"price": "1"}}}))
    assert client.fetch_prices() == {"FOO": {"price": "1"}}


def test_fetch_prices_empty_on_unexpected():
    client = AlphaClient(session=FakeSession([1, 2, 3]))
    assert client.fetch_prices() == {}


def test_timeout_passed_through():
    session = FakeSession([])
    AlphaClient(timeout=7, session=session).fetch_airdrops()
    url, headers, timeout = session.calls[0]
    assert url == "https://alpha123.uk/api/data?fresh=1"  # parity tripwire
    assert headers == HEADERS
    assert timeout == 7
