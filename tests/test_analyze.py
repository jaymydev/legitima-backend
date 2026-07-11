from fastapi.testclient import TestClient

from app.main import app


def test_analyze_requires_expected_payload_shape() -> None:
    client = TestClient(app)
    response = client.post("/analyze", json={"input": {"meta": {}}})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_analyze_accepts_current_ios_payload_shape() -> None:
    client = TestClient(app)
    payload = {
        "input": {
            "meta": {
                "version": "1.0",
                "language": "fr",
                "target_market": "US",
                "interview_type": "recruitment",
            },
            "narrative_positioning": {
                "short_summary": "Resume",
                "current_positioning": "Backend engineer",
                "evolution_logic": "Bench periods reframed as skill-building",
            },
        }
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "OPENAI_API_KEY environment variable is missing"}
