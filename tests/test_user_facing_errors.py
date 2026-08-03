"""The error contract: French prose for the person, a stable code for the client.

Every route the iOS app calls can fail, and when it does the app prints the
response's `detail` in red, unchanged, to someone about to walk into an
interview. So two things have to hold, and both are easy to undo with an
ordinary-looking `raise`:

  1. the sentence is French, and addressed to that person;
  2. `detail` stays a plain string, so a client that only reads it keeps
     working, with `code` added beside it rather than inside it.

The third test is the one that matters. Asserting the messages currently in the
catalog proves nothing about the next `raise HTTPException(...)` someone adds —
so it reads the source of the three modules the app talks to instead.
"""

from __future__ import annotations

import ast
import io
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import errors
from app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Modules whose raises can end up on someone's screen.
USER_FACING_MODULES = (
    "app/services/cv_parse.py",
    "app/api/routes/analyze.py",
    "app/api/routes/interview_preparation.py",
)

#: (module, function) allowed to raise a bare HTTPException, and why.
ALLOWED_BARE_RAISES = {
    # A forced 500 gated behind ENABLE_CV_PARSE_TEST_ERRORS, there to exercise
    # the client's error path. Unreachable in production, so never read.
    ("app/services/cv_parse.py", "maybe_raise_cv_parse_test_error"),
}

#: English words with no French homograph. Two of them is not an accident.
ENGLISH_MARKERS = (
    "the",
    "is",
    "was",
    "were",
    "this",
    "that",
    "with",
    "your",
    "upload",
    "found",
    "failed",
    "missing",
    "invalid",
    "unsupported",
    "could",
    "should",
    "please",
    "again",
    "readable",
)

#: French function words. Two of them means the sentence is French.
FRENCH_MARKERS = (
    "avec",
    "ce",
    "cette",
    "dans",
    "de",
    "du",
    "en",
    "est",
    "et",
    "être",
    "la",
    "le",
    "les",
    "ne",
    "pas",
    "pour",
    "puis",
    "que",
    "quelques",
    "sur",
    "une",
    "un",
    "votre",
    "vous",
)


def _word_hits(text: str, words: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [word for word in words if re.search(rf"\b{re.escape(word)}\b", lowered)]


@pytest.mark.parametrize("code", sorted(errors._CATALOG))
def test_every_message_is_french_and_tells_the_reader_what_to_do(code: str) -> None:
    _, message = errors._CATALOG[code]

    english = _word_hits(message, ENGLISH_MARKERS)
    assert len(english) < 2, f"{code} reads as English: {english} in {message!r}"

    french = _word_hits(message, FRENCH_MARKERS)
    assert len(french) >= 2, f"{code} does not read as French: {message!r}"

    # Two sentences: what happened, and what to do about it. A message that
    # only names the failure leaves the reader stuck.
    assert message.count(".") >= 2, f"{code} suggests no next step: {message!r}"


def test_the_body_keeps_detail_a_string_and_puts_the_code_beside_it() -> None:
    """The shape 1.0.1 decodes: `detail` a string, extra keys ignored.

    Moving the code *inside* `detail` would be the tempting one-line version of
    this change, and it would blank the message on every client already
    shipped — they decode `detail` as a string or not at all.
    """
    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415
    body = response.json()
    assert set(body) == {"detail", "code"}
    assert isinstance(body["detail"], str)
    assert body["code"] == errors.CV_UNSUPPORTED_FILE_TYPE


def test_a_malformed_body_is_refused_in_french_with_the_fields_named() -> None:
    """FastAPI's own `422` used to answer `[{"msg": "Field required"}]`.

    The client reads the first `msg`, so a client bug printed English at the
    user. The field list is still there, under `fields`, for whoever is
    debugging the client.
    """
    response = TestClient(app).post("/analyze", json={"input": {"meta": {}}})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == errors.INVALID_REQUEST
    assert isinstance(body["detail"], str)
    assert "Field required" not in response.text
    assert "body.input.narrative_positioning" in body["fields"]


def test_the_file_size_limit_is_quoted_from_the_constant() -> None:
    """The message says "10 Mo" because the constant says 10 MiB, not because
    someone typed it."""
    oversized = b"a" * (10 * 1024 * 1024 + 1)

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(oversized), "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["code"] == errors.CV_FILE_TOO_LARGE
    assert "10 Mo" in response.json()["detail"]


@pytest.mark.parametrize("module", USER_FACING_MODULES)
def test_no_user_facing_route_raises_a_bare_http_exception(module: str) -> None:
    """A bare `raise HTTPException(...)` here means English on someone's screen.

    Catching it by asserting today's messages would not work: the next one
    added would pass every existing test while shipping English. This reads the
    source, so a new raise fails until it goes through the catalog.
    """
    path = REPO_ROOT / module
    tree = ast.parse(path.read_text(encoding="utf-8"))

    exempt_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (module, node.name) in ALLOWED_BARE_RAISES:
                exempt_lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))

    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and _called_name(node.exc.func) == "HTTPException"
        and node.lineno not in exempt_lines
    ]

    assert not offenders, (
        f"{module} raises HTTPException directly at line(s) {offenders}. "
        "Use user_facing_error(CODE) so the caller is told something in French."
    )


def _called_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None
