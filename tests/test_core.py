from datetime import datetime, timedelta, timezone

from alpha_notify.core import check_for_updates
from alpha_notify.errors import AlphaNotifyError
from alpha_notify.models import select_today_airdrops
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


class _FailingNotifier:
    def send(self, title, body):
        raise AlphaNotifyError("send boom")


class _PriceFailClient:
    def __init__(self, airdrops):
        self._a = airdrops

    def fetch_airdrops(self):
        return self._a

    def fetch_prices(self):
        raise AlphaNotifyError("price boom")


def test_send_failure_not_marked_sent(tmp_path):
    # If sending fails, the airdrop must NOT be recorded as sent (no false dedup).
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    store = NotificationStore(tmp_path / "n.db")
    check_for_updates(client=client, store=store, notifier=_FailingNotifier(),
                      cache_path=tmp_path / "c.json", now=NOW)
    _, today_airdrops, _ = select_today_airdrops(
        client.fetch_airdrops(), client.fetch_prices(), NOW
    )
    assert [a.identity for a in store.filter_unsent(today_airdrops)] == ["1"]


def test_force_does_not_write_db(tmp_path):
    # force sends but must not poison the dedup DB → a later normal run still sends.
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    store = NotificationStore(tmp_path / "n.db")
    cache_path = tmp_path / "c.json"
    check_for_updates(client=client, store=store, notifier=FakeNotifier(),
                      cache_path=cache_path, now=NOW, force=True)
    notifier2 = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=notifier2,
                      cache_path=cache_path, now=NOW)
    assert len(notifier2.sent) == 1


def test_no_store_still_sends(tmp_path):
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    notifier = FakeNotifier()
    check_for_updates(client=client, store=None, notifier=notifier,
                      cache_path=tmp_path / "c.json", now=NOW)
    assert len(notifier.sent) == 1


def test_price_failure_degrades_and_sends(tmp_path):
    # A price-fetch failure degrades to no prices but still sends the airdrop.
    client = _PriceFailClient([_record("1")])
    notifier = FakeNotifier()
    check_for_updates(client=client, store=None, notifier=notifier,
                      cache_path=tmp_path / "c.json", now=NOW)
    assert len(notifier.sent) == 1


class _CleanupFailStore(NotificationStore):
    def cleanup(self, current_date):
        raise AlphaNotifyError("cleanup boom")


def test_cleanup_failure_keeps_dedup(tmp_path):
    client = FakeClient([_record("1")], {"FOO": {"price": "2"}})
    store = _CleanupFailStore(tmp_path / "n.db")
    cache_path = tmp_path / "c.json"

    n1 = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=n1,
                      cache_path=cache_path, now=NOW)
    assert len(n1.sent) == 1  # sent despite cleanup failing

    n2 = FakeNotifier()
    check_for_updates(client=client, store=store, notifier=n2,
                      cache_path=cache_path, now=NOW)
    assert n2.sent == []  # dedup still active -> not re-sent
