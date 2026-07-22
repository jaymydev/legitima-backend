import io
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.services import cv_parse as cv_parse_service


def test_cv_parse_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/cv/parse",
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"].startswith("Unsupported file type")


def test_cv_parse_requires_openai_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/cv/parse",
        files={"file": ("resume.png", io.BytesIO(b"fake-image"), "image/png")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "OPENAI_API_KEY environment variable is missing"}


def test_cv_parse_extracts_experiences_from_pdf(monkeypatch) -> None:
    client = TestClient(app)
    expected_response = {
        "experiences": [
            {
                "title": "Senior Backend Engineer",
                "company": "Legitima",
                "period": "2023-2026",
            }
        ]
    }

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(expected_response)))]
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cv_parse_service, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        cv_parse_service,
        "_extract_text_from_pdf",
        lambda _: "Senior Backend Engineer - Legitima - 2023-2026",
    )

    response = client.post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == expected_response


def test_cv_parse_rejects_pdf_without_extractable_text(monkeypatch) -> None:
    client = TestClient(app)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cv_parse_service, "_extract_text_from_pdf", lambda _: "")

    response = client.post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 422
    assert "No extractable text was found in the PDF" in response.json()["detail"]


def test_cv_parse_rejects_oversized_files(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    oversized_bytes = b"a" * (cv_parse_service.MAX_CV_FILE_SIZE_BYTES + 1)
    response = client.post(
        "/cv/parse",
        files={"file": ("resume.png", io.BytesIO(oversized_bytes), "image/png")},
    )

    assert response.status_code == 413
    assert "Maximum size is" in response.json()["detail"]
