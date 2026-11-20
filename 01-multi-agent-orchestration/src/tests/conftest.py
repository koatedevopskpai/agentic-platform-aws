"""Keep the unit tests offline and deterministic.

Without this, the news tool calls the real newsapi.org with a demo key and the result depends on the network.
The default fake answers HTTP 503; a test can replace `mock_http["handler"]` to return something else.
"""

import httpx
import pytest

_REAL_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture(autouse=True)
def mock_http(monkeypatch):
    state = {"handler": lambda request: httpx.Response(503)}

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(lambda request: state["handler"](request))
        return _REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return state
