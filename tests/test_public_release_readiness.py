"""Gates for making this repository public and leaving the API exposed.

The service has no authentication: anyone who extracts the base URL from the
iOS binary can call it. Three properties have to hold, and each is easy to
break silently with an ordinary-looking change:

  1. every handler that spends OpenAI tokens is rate limited;
  2. nothing internal — API keys, prompts, upstream error text — reaches the
     caller in an error body;
  3. no secret is committed.

These are cheap to assert and expensive to discover in the wild.
"""

from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import rate_limit
from app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent

ANALYZE_BODY = {
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


def _route_limit_names() -> set[str]:
    return set(app.state.limiter._route_limits)


def _endpoint_name(endpoint) -> str:
    return f"{endpoint.__module__}.{endpoint.__name__}"


def test_every_handler_that_calls_openai_declares_an_explicit_limit() -> None:
    """The rule, enforced against the source rather than a hand-kept list.

    A new AI endpoint would still fall under the 120/hour default, which is
    twelve times more OpenAI calls per hour than intended. This fails the
    moment such a handler is added without its own decorator.
    """
    registered = _route_limit_names()
    unlimited = []

    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        try:
            source = inspect.getsource(inspect.unwrap(endpoint))
        except (OSError, TypeError):
            continue
        if "OpenAI(" not in source:
            continue
        if _endpoint_name(endpoint) not in registered:
            unlimited.append(route.path)

    assert not unlimited, (
        f"these handlers spend OpenAI tokens with no explicit limit: {unlimited}"
    )


def test_a_failing_upstream_call_never_echoes_the_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI answers a bad key with `Incorrect API key provided: sk-...`.

    Interpolating that exception into an HTTP detail hands the key to whoever
    asked. Nothing upstream should reach the caller; it belongs in the log.
    """
    secret = "sk-thisisthesecretkeyvalue"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    class ExplodingClient:
        def __init__(self, *args, **kwargs) -> None:
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, *args, **kwargs):
            raise RuntimeError(f"Incorrect API key provided: {secret}")

    monkeypatch.setattr("app.api.routes.analyze.OpenAI", ExplodingClient)

    response = TestClient(app, raise_server_exceptions=False).post(
        "/analyze", json=ANALYZE_BODY, headers={"X-Forwarded-For": "198.51.100.20"}
    )

    assert response.status_code >= 500
    assert secret not in response.text
    assert "sk-" not in response.text


def test_a_malformed_model_reply_never_echoes_the_prompt_or_the_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The model's raw output is derived from the user's career text. Echoing
    it back inside a parse error would put that content in logs and proxies
    that never needed it."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-irrelevant")
    marker = "CONFIDENTIALCAREERDETAIL"

    class Message:
        content = f"not json at all {marker}"

    class Choice:
        message = Message()

    class Completion:
        choices = [Choice()]

    class Client:
        def __init__(self, *args, **kwargs) -> None:
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, *args, **kwargs):
            return Completion()

    monkeypatch.setattr("app.api.routes.analyze.OpenAI", Client)

    response = TestClient(app, raise_server_exceptions=False).post(
        "/analyze", json=ANALYZE_BODY, headers={"X-Forwarded-For": "198.51.100.21"}
    )

    assert response.status_code >= 400
    assert marker not in response.text


def test_the_refusal_body_says_only_that_a_limit_was_hit() -> None:
    """A 429 is served to unauthenticated callers by definition. It must not
    become a channel for anything else."""
    client = TestClient(app)
    headers = {"X-Forwarded-For": "198.51.100.30"}
    body = {
        "context": {
            "target_role": "",
            "career_experiences": "",
            "sensitive_point": "",
            "freemium_analysis": "",
        }
    }

    refused = None
    for _ in range(13):
        response = client.post(
            "/v2/interview-preparation/kickoff", json=body, headers=headers
        )
        if response.status_code == 429:
            refused = response
            break

    assert refused is not None, "the kickoff limit never fired"
    assert refused.json() == {"error": "Rate limit exceeded: 10 per 1 hour"}
    assert refused.headers.get("retry-after")


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),          # OpenAI keys
    re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\."),         # JWTs, e.g. Supabase
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
)

# Files whose job is to describe the shapes above.
SCAN_EXCLUDED = {"tests/test_public_release_readiness.py"}


def test_no_tracked_file_contains_a_secret() -> None:
    """Runs against what git actually tracks, which is what publishing
    exposes — including files an editor added without anyone noticing."""
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    offenders = []
    for relative in tracked:
        if relative in SCAN_EXCLUDED:
            continue
        path = REPO_ROOT / relative
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                offenders.append(f"{relative} matches {pattern.pattern}")

    assert not offenders, "\n".join(offenders)


def test_no_env_file_is_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    assert not [name for name in tracked if Path(name).name.startswith(".env")]


def test_health_stays_exempt_so_render_cannot_take_the_service_down() -> None:
    client = TestClient(app)
    headers = {"X-Forwarded-For": "198.51.100.40"}
    for _ in range(150):  # past DEFAULT_LIMIT
        assert client.get("/health", headers=headers).status_code == 200


def test_the_limits_are_the_documented_ones() -> None:
    """These numbers are published in docs/api-contract.md and README.md.
    Changing one without the other leaves the contract lying."""
    contract = (REPO_ROOT / "docs" / "api-contract.md").read_text(encoding="utf-8")
    assert rate_limit.AI_GENERATION_LIMIT == "10/hour"
    assert rate_limit.CV_PARSE_LIMIT == "20/hour"
    assert rate_limit.DEFAULT_LIMIT == "120/hour"
    assert "10 / hour" in contract
    assert "20 / hour" in contract
    assert "120 / hour" in contract
