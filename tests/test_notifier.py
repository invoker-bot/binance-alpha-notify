import pytest

from alpha_notify.errors import AlphaNotifyError
from alpha_notify.notifier import Notifier


class FakeApprise:
    def __init__(self, asset=None):
        self.added = []
        self.notified = None

    def add(self, url):
        self.added.append(url)
        return True

    def __len__(self):
        return len(self.added)

    def notify(self, title, body):
        self.notified = (title, body)
        return self._result if hasattr(self, "_result") else True


def _patch_apprise(monkeypatch, result=True):
    import alpha_notify.notifier as nmod

    def factory(asset=None):
        inst = FakeApprise(asset=asset)
        inst._result = result
        return inst

    monkeypatch.setattr(nmod.apprise, "Apprise", factory)
    monkeypatch.setattr(nmod.apprise, "AppriseAsset", lambda **kw: object())


def test_send_no_urls_raises():
    with pytest.raises(AlphaNotifyError):
        Notifier([]).send("t", "b")


def test_send_success(monkeypatch):
    _patch_apprise(monkeypatch, result=True)
    assert Notifier(["x://y"]).send("t", "b") == 1


def test_send_failure_raises(monkeypatch):
    _patch_apprise(monkeypatch, result=False)
    with pytest.raises(AlphaNotifyError):
        Notifier(["x://y"]).send("t", "b")
