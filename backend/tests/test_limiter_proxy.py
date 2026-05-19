import os
import sys
import importlib
from types import SimpleNamespace

# Ensure backend dir is on sys.path so tests can import local modules
HERE = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def _make_req(headers=None, host="10.0.0.1"):
    class Dummy:
        def __init__(self, headers, host):
            self.headers = headers or {}
            self.client = SimpleNamespace(host=host)

    return Dummy(headers or {}, host)


def test_default_ignores_xff(monkeypatch):
    # Ensure env var is not set, then (re)load limiter
    monkeypatch.delenv("USE_PROXY_HEADERS", raising=False)
    import limiter
    importlib.reload(limiter)

    req = _make_req({"X-Forwarded-For": "1.2.3.4"}, host="10.0.0.1")
    key = limiter.key_func(req)
    assert key == "ip:10.0.0.1"


def test_proxy_enabled_uses_xff(monkeypatch):
    monkeypatch.setenv("USE_PROXY_HEADERS", "true")
    import importlib as _importlib
    import limiter as _limiter
    _importlib.reload(_limiter)

    req = _make_req({"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}, host="10.0.0.1")
    key = _limiter.key_func(req)
    assert key == "ip:1.2.3.4"
