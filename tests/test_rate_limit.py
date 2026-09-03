"""The per-IP limit is the only thing between a loop and the OpenAI account.

Two failure modes matter more than the counting itself:
  - keying on the socket peer would put every user behind Render's proxy in
    one bucket, and the app would start refusing real traffic;
  - keying on anything the platform varies per request — such as the rightmost
    `X-Forwarded-For` entry, which is what this originally used — gives every
    call a fresh bucket, and the limit stops limiting. The tell was
    `X-RateLimit-Remaining` climbing back up between requests.
The second one is the reason `test_the_key_is_stable_across_requests` exists:
no unit test can see the deployed proxy, but it can pin the rule that the key
must come from a position the platform does not rotate.
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


def test_client_ip_reads_the_client_end_of_the_chain() -> None:
    # Render appends its own hop, and that address changes between requests.
    # Reading from the right therefore produced a new bucket per call. The
    # client sits on the left and is stable, which is what a counter needs.
    chain = {"X-Forwarded-For": "203.0.113.7, 10.11.12.13"}
    assert _client_ip(chain) == "203.0.113.7"


def test_the_key_is_stable_across_requests() -> None:
    """The property the original version failed: the same caller must key to
    the same bucket even when the platform's own hop rotates."""
    keys = {
        _client_ip({"X-Forwarded-For": f"203.0.113.7, 10.11.12.{tail}"})
        for tail in range(20)
    }
    assert keys == {"203.0.113.7"}


def test_client_ip_can_skip_leading_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIPPED_FORWARDED_ENTRIES", "1")
    assert _client_ip({"X-Forwarded-For": "1.1.1.1, 203.0.113.7, 10.0.0.9"}) == "203.0.113.7"

    # A header shorter than the configured depth must still yield an address
    # rather than raise: an IndexError here would 500 every request.
    assert _client_ip({"X-Forwarded-For": "203.0.113.7"}) == "203.0.113.7"

    monkeypatch.setenv("SKIPPED_FORWARDED_ENTRIES", "not-a-number")
    assert _client_ip({"X-Forwarded-For": "203.0.113.7, 10.0.0.9"}) == "203.0.113.7"


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


def test_a_rotating_platform_hop_does_not_buy_a_fresh_quota() -> None:
    """The exact production failure, in a test.

    Render appends a hop whose address differs from one request to the next.
    Keyed on that, each call opened a new bucket and the limit never fired.
    """
    client = TestClient(_isolated_app("2/hour"))

    for index in range(2):
        client.get("/costly", headers={"X-Forwarded-For": f"203.0.113.7, 10.11.12.{index}"})

    refused = client.get("/costly", headers={"X-Forwarded-For": "203.0.113.7, 10.11.12.99"})
    assert refused.status_code == 429


def test_a_forged_leading_entry_is_a_known_and_accepted_weakness() -> None:
    """Keying on the client end means a caller who forges it gets a new
    bucket. Pinned deliberately, so nobody reads it as an oversight: the
    alternative measured in production was a limit that applied to no one,
    and the real backstop is the OpenAI monthly spend cap.
    """
    client = TestClient(_isolated_app("2/hour"))

    for _ in range(3):
        client.get("/costly", headers={"X-Forwarded-For": "203.0.113.7"})

    assert (
        client.get("/costly", headers={"X-Forwarded-For": "203.0.113.8"}).status_code == 200
    )


def test_health_is_never_counted() -> None:
    """Render polls /health continuously. Counting it would exhaust the
    default bucket unaided and take the service down."""
    from app.main import app

    client = TestClient(app)
    headers = {"X-Forwarded-For": "203.0.113.250"}
    for _ in range(200):  # far past DEFAULT_LIMIT
        assert client.get("/health", headers=headers).status_code == 200


def test_analyze_refuses_the_call_past_the_budget_from_one_address(
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
    for _ in range(_hourly_budget(rate_limit.AI_GENERATION_LIMIT)):
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
    assert rate_limit.AI_GENERATION_LIMIT == "30/hour"
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


def _hourly_budget(limit: str) -> int:
    """The count out of a `limits` string such as `30/hour`.

    Derived rather than written twice, so a test cannot keep asserting a
    budget the module no longer grants.
    """
    return int(limit.split("/", 1)[0])


def test_the_route_the_app_uses_is_rate_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`/v3/interview/questions` is the only limited route with a live client.

    A dropped decorator is already caught, by
    `test_every_handler_that_calls_openai_declares_an_explicit_limit`, which
    reads the source. What reading the source cannot show is whether the limit
    *fires*: that also needs slowapi's wrapper to run, the catch-all
    `Exception` handler not to swallow the refusal into a 500 — retry now —
    instead of a 429, and `Retry-After` to be emitted, which the app reads to
    tell someone how long the wait is. The only end-to-end check of that kind
    ran against `/analyze`, a route with no client left.

    The budget is read from the constant, so this exercises whatever the
    module currently grants rather than a number copied here once.
    """
    from app.main import app
    from app.services import interview_questions as service

    # No key: the handler stops before OpenAI, so this needs no network. It
    # still reaches the handler, which is what being counted requires.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)
    headers = {"X-Forwarded-For": "203.0.113.31"}
    body = {
        "use_case_id": "performance_review",
        "questionnaire_version": service.QUESTIONS_VERSION,
    }

    budget = _hourly_budget(rate_limit.AI_GENERATION_LIMIT)
    for index in range(budget):
        spent = client.post("/v3/interview/questions", json=body, headers=headers)
        assert spent.status_code != 429, f"refused at call {index + 1} of {budget}"

    refused = client.post("/v3/interview/questions", json=body, headers=headers)
    assert refused.status_code == 429, "the route's own limit never fired"
    assert refused.headers.get("retry-after")
