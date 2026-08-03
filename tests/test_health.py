from fastapi.testclient import TestClient

from app.main import app
from app.services.cv_parse import ocr_availability


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_whether_ocr_can_actually_run() -> None:
    """The field exists because its absence shipped to production.

    Two Render services ran this repository: one on the native Python runtime,
    one from the Dockerfile. Both installed pytesseract; only the Docker one
    had the `tesseract` binary. Every route answered identically until a real
    photo arrived, and CV import returned 500 for days before anyone noticed.
    One call to /health now says which machine you are talking to.
    """
    body = TestClient(app).get("/health").json()

    assert "ocr" in body
    assert isinstance(body["ocr"]["available"], bool)

    if body["ocr"]["available"]:
        assert body["ocr"]["engine_version"]
        assert body["ocr"]["languages"]
    else:
        # Never silently false: say why, so a deploy can be diagnosed remotely.
        assert body["ocr"]["reason"]


def test_ocr_availability_never_raises() -> None:
    """/health must answer even where OCR is broken — it is what Render polls
    to decide the service is alive."""
    result = ocr_availability()
    assert isinstance(result, dict)
    assert "available" in result
