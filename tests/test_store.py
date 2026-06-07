from datetime import datetime, timedelta, timezone

from alpha_notify.models import Airdrop
from alpha_notify.store import NotificationStore

BJ = timezone(timedelta(hours=8))
NOW = datetime(2026, 6, 8, 10, 0, 0, tzinfo=BJ)


def _drop(identity, date="2026-06-08"):
    return Airdrop(identity=identity, token="T", date=date, time="15:00",
                   amount="1", points="1", price=None, dex_price=None, scheduled_at=NOW)


def test_filter_unsent_and_mark(tmp_path):
    store = NotificationStore(tmp_path / "n.db")
    drops = [_drop("a"), _drop("b")]
    assert {d.identity for d in store.filter_unsent(drops)} == {"a", "b"}
    store.mark_sent([_drop("a")], NOW)
    assert [d.identity for d in store.filter_unsent(drops)] == ["b"]


def test_mark_sent_empty_is_noop(tmp_path):
    store = NotificationStore(tmp_path / "n.db")
    store.mark_sent([], NOW)  # must not raise
    assert store.filter_unsent([]) == []


def test_cleanup_removes_other_dates(tmp_path):
    store = NotificationStore(tmp_path / "n.db")
    store.mark_sent([_drop("old", date="2026-06-01")], NOW)
    store.cleanup("2026-06-08")
    again = store.filter_unsent([_drop("old", date="2026-06-01")])
    assert [d.identity for d in again] == ["old"]


def test_store_creates_missing_parent_dir(tmp_path):
    store = NotificationStore(tmp_path / "sub" / "deep" / "n.db")
    store.mark_sent([_drop("a")], NOW)
    assert [d.identity for d in store.filter_unsent([_drop("a")])] == []


def test_store_releases_db_file(tmp_path):
    import os
    db = tmp_path / "n.db"
    store = NotificationStore(db)
    store.mark_sent([_drop("a")], NOW)
    store.filter_unsent([_drop("a")])
    os.remove(db)  # must not raise: no lingering open connection (Windows file lock)
    assert not db.exists()
