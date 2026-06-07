from datetime import datetime, timedelta, timezone

from alpha_notify.core import check_for_updates
from alpha_notify.store import NotificationStore

BJ = timezone(timedelta(hours=8))
NOW = datetime(2026, 6, 8, 10, 0, 0, tzinfo=BJ)


class FakeClient:
    def __init__(self, airdrops, prices=None):
        self._a = airdrops
        self._p = prices or {}

    def fetch_airdrops(self):
        return self._a

    def fetch_prices(self):
        return self._p


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, title, body):
        self.sent.append((title, body))
        return 1


def _record(identity="1", time="15:00"):
    return {"id": identity, "token": "FOO", "date": "2026-06-08", "time": time,
            "amount": "100", "points": "200"}


def test_sends_then_dedups(tmp_path):
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    store = NotificationStore(tmp_path / "n.db")
    cache_path = tmp_path / "c.json"

    notifier1 = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=notifier1,
                      cache_path=cache_path, now=NOW)
    assert len(notifier1.sent) == 1

    notifier2 = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=notifier2,
                      cache_path=cache_path, now=NOW)
    assert notifier2.sent == []


def test_force_bypasses_dedup(tmp_path):
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    store = NotificationStore(tmp_path / "n.db")
    cache_path = tmp_path / "c.json"
    notifier = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=notifier,
                      cache_path=cache_path, now=NOW, force=True)
    assert len(notifier.sent) == 1


def test_dry_run_does_not_send(tmp_path):
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    notifier = FakeNotifier()
    log = check_for_updates(client=client, store=None, notifier=notifier,
                            cache_path=tmp_path / "c.json", now=NOW, dry_run=True)
    assert notifier.sent == []
    assert "dry-run" in log
    assert not (tmp_path / "c.json").exists()


def test_no_airdrops_skips(tmp_path):
    client = FakeClient([_record("1", time="待定")])
    notifier = FakeNotifier()
    check_for_updates(client=client, store=None, notifier=notifier,
                      cache_path=tmp_path / "c.json", now=NOW)
    assert notifier.sent == []
