import alpha_notify
from alpha_notify.errors import AlphaNotifyError


def test_version_is_exposed():
    assert isinstance(alpha_notify.__version__, str)
    assert alpha_notify.__version__


def test_error_type_exists():
    assert issubclass(AlphaNotifyError, Exception)
