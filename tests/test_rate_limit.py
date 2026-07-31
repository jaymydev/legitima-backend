"""The per-IP limit is the only thing between a loop and the OpenAI account.

Two failure modes matter more than the counting itself:
  - keying on the socket peer would put every user behind Render's proxy in
    one bucket, and the app would start refusing real traffic;
  - trusting the left of `X-Forwarded-For` would let a caller mint a fresh
    quota per request by forging a header.
Both are covered below.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api import rate_limit


def _client_ip(headers: dict, peer: str = "10.0.0.1") -> str:
    scope = {
        "type": "http",
        "client": (peer, 1234),
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return rate_limit.client_ip(Request(scope))


def test_client_ip_falls_back_to_the_socket_peer() -> None:
    assert _client_ip({}) == "10.0.0.1"


def test_client_ip_reads_the_forwarded_header_when_present() -> None:
    assert _client_ip({"X-Forwarded-For": "203.0.113.7"}) == "203.0.113.7"
    assert _client_ip({"X-Forwarded-For": " 203.0.113.7 "}) == "203.0.113.7"


def test_client_ip_ignores_addresses_the_caller_prepended() -> None:
    # Each hop appends, so anything a caller forges lands on the left. Reading
    # from the left would hand out a fresh quota for every invented address.
    forged = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 203.0.113.7"}
    assert _client_ip(forged) == "203.0.113.7"


def test_client_ip_honours_the_trusted_hop_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
    assert _client_ip({"X-Forwarded-For": "1.1.1.1, 203.0.113.7, 10.0.0.9"}) == "203.0.113.7"

    # A header shorter than the configured depth must still yield an address
    # rather than raise: an IndexError here would 500 every request.
    assert _client_ip({"X-Forwarded-For": "203.0.113.7"}) == "203.0.113.7"

    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "not-a-number")
    assert _client_ip({"X-Forwarded-For": "1.1.1.1, 203.0.113.7"}) == "203.0.113.7"


def _isolated_app(limit: str) -> FastAPI:
    """A one-route app with its own counters.

    Built from a fresh `Limiter` rather than by reloading the module: reloading
    would swap the instance the real app registered its routes against, and
    these tests would then pass or fail depending on their order.
    """
    isolated = Limiter(key_func=rate_limit.client_ip, headers_enabled=True)
    app = FastAPI()
    app.state.limiter = isolated
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/costly")
    @isolated.limit(limit)
    def costly(request: Request, response: Response):
        return {"ok": True}

    return app


def test_the_limit_answers_429_once_the_budget_is_spent() -> None:
    client = TestClient(_isolated_app("3/hour"))
    headers = {"X-Forwarded-For": "203.0.113.7"}

    for _ in range(3):
        assert client.get("/costly", headers=headers).status_code == 200

    refused = client.get("/costly", headers=headers)
    assert refused.status_code == 429
    # The catch-all `Exception` handler must not swallow this into a 500:
    # a 429 tells the caller to wait, a 500 tells them to retry immediately.
    assert "Rate limit exceeded" in refused.text
    assert "retry-after" in {k.lower() for k in refused.headers}


def test_one_caller_hitting_the_limit_does_not_block_another() -> None:
    client = TestClient(_isolated_app("2/hour"))

    for _ in range(2):
        client.get("/costly", headers={"X-Forwarded-For": "203.0.113.7"})
    assert client.get("/costly", headers={"X-Forwarded-For": "203.0.113.7"}).status_code == 429

    # The whole point of keying per IP: everybody else is unaffected.
    assert client.get("/costly", headers={"X-Forwarded-For": "198.51.100.4"}).status_code == 200


def test_forging_the_header_does_not_buy_a_fresh_quota() -> None:
    client = TestClient(_isolated_app("2/hour"))

    for index in range(2):
        client.get("/costly", headers={"X-Forwarded-For": f"9.9.9.{index}, 203.0.113.7"})

    refused = client.get("/costly", headers={"X-Forwarded-For": "9.9.9.42, 203.0.113.7"})
    assert refused.status_code == 429


def test_health_is_never_counted() -> None:
    """Render polls /health continuously. Counting it would exhaust the
    default bucket unaided and take the service down."""
    from app.main import app

    client = TestClient(app)
    headers = {"X-Forwarded-For": "203.0.113.250"}
    for _ in range(200):  # far past DEFAULT_LIMIT
        assert client.get("/health", headers=headers).status_code == 200


def test_analyze_refuses_the_eleventh_call_from_one_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end on the real app, which registers a catch-all `Exception`
    handler. If that handler ever caught RateLimitExceeded the caller would
    read 500 — retry now — instead of 429 with a Retry-After."""
    from app.main import app

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)
    headers = {"X-Forwarded-For": "203.0.113.99"}
    body = {
        "input": {
            "meta": {
                "version": "1.0",
                "language": "fr",
                "target_market": "FR",
                "interview_type": "recruitment",
            },
            "narrative_positioning": {
                "short_summary": "s",
                "current_positioning": "p",
                "evolution_logic": "e",
            },
        }
    }

    # 500 here means the handler ran and was counted: the missing API key is
    # rejected inside the route, past the limiter.
    for _ in range(10):
        assert client.post("/analyze", json=body, headers=headers).status_code == 500

    refused = client.post("/analyze", json=body, headers=headers)
    assert refused.status_code == 429
    assert refused.headers.get("retry-after") == "3600"

    assert (
        client.post(
            "/analyze", json=body, headers={"X-Forwarded-For": "198.51.100.9"}
        ).status_code
        == 500
    )


def test_the_expensive_routes_declare_a_limit() -> None:
    """A new AI endpoint added without a decorator still falls under the
    blanket default, but these four are the ones that cost tokens."""
    assert rate_limit.AI_GENERATION_LIMIT == "10/hour"
    assert rate_limit.CV_PARSE_LIMIT == "20/hour"
    assert rate_limit.DEFAULT_LIMIT == "120/hour"

    from app.main import app

    # Read the limiter the app actually wired up, not the module global, so
    # this cannot be fooled by import order.
    registered = app.state.limiter._route_limits
    limited = set()
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        if f"{endpoint.__module__}.{endpoint.__name__}" in registered:
            limited.add(route.path)

    for path in (
        "/analyze",
        "/cv/parse",
        "/v2/interview-preparation/analyze",
        "/v2/interview-preparation/kickoff",
    ):
        assert path in limited, f"{path} lost its rate limit"
