import io

from fastapi.testclient import TestClient

from app.main import app
from app.services import cv_parse as cv_parse_service


def test_cv_parse_rejects_unsupported_file_type() -> None:
    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415


def test_cv_parse_test_error_header_is_ignored_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_CV_PARSE_TEST_ERRORS", raising=False)

    response = TestClient(app).post(
        "/cv/parse",
        headers={"X-CV-Parse-Test-Error": "500"},
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415


def test_cv_parse_can_force_500_when_test_errors_are_enabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_CV_PARSE_TEST_ERRORS", "true")

    response = TestClient(app).post(
        "/cv/parse",
        headers={"X-CV-Parse-Test-Error": "500"},
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Forced /cv/parse test error"}


def test_cv_parse_rejects_images_without_using_openai() -> None:
    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.png", io.BytesIO(b"fake-image"), "image/png")},
    )

    assert response.status_code == 422
    assert "text-based PDF" in response.json()["detail"]


def test_cv_parse_extracts_structured_experience_and_excludes_other_sections() -> None:
    text = """
    FORMATIONS
    Master 2017 - 2019
    EXPÉRIENCES PROFESSIONNELLES
    AIRBUS
    Développeur logiciel - 2024
    THALES ALENIA SPACE
    Développeur logiciel - 2022 à 2023
    COMPÉTENCES
    Python Git Leadership
    LANGUES
    Français Anglais
    """

    result = cv_parse_service.parse_cv_text(text)

    assert result.model_dump() == {
        "experiences": [
            {"title": "Développeur logiciel", "company": "AIRBUS", "period": "2024"},
            {"title": "Développeur logiciel", "company": "THALES ALENIA SPACE", "period": "2022 à 2023"},
        ]
    }


def test_cv_parse_supports_company_title_period_on_one_line() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        PARCOURS PROFESSIONNEL
        DOMINO STAFF pour OCEA Smart Building - Assistante d'exploitation
        22/09/20 à aujourd'hui
        FORMATIONS
        AFPA 2017 - 2018
        """
    )

    assert result.experiences == [
        cv_parse_service.CVExperience(
            title="Assistante d'exploitation",
            company="DOMINO STAFF pour OCEA Smart Building",
            period="22/09/20 à aujourd'hui",
        )
    ]


def test_cv_parse_handles_english_role_lines_without_promoting_bullets() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        Experience
        PLM Engineer - Confidential Program (High-Security Sector) | Jan 2026 - Present
        - Building secure 3DEXPERIENCE widgets for a regulated, defense-related environment.
        - Improved PLM automation and reduced manual workload ~15-20%.
        PLM Technical Consultant - Airbus (via Capgemini) | 2024
        Software Engineer - AI Internal Project (Capgemini) | 2025
        Software & Test Engineer - Aerospace/Automotive Programs | 2017-2023
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "PLM Engineer",
                "company": "Confidential Program (High-Security Sector)",
                "period": "Jan 2026 - Present",
            },
            {
                "title": "PLM Technical Consultant",
                "company": "Airbus (via Capgemini)",
                "period": "2024",
            },
            {
                "title": "Software Engineer",
                "company": "AI Internal Project (Capgemini)",
                "period": "2025",
            },
            {
                "title": "Software & Test Engineer",
                "company": "Aerospace/Automotive Programs",
                "period": "2017-2023",
            },
        ]
    }


def test_cv_parse_joins_company_mission_continuation_lines() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPERIENCES PROFESSIONNELLES
        Consultante Senior – Transition & Team Lead  Accenture (Mission Airbus
        — Customer Services) | Janv. 2023 – Nov. 2024
        ●Contexte :  Cadrage, optimisation et transfert d'activités critiques vers des
        équipes offshore
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "Consultante Senior - Transition & Team Lead",
                "company": "Accenture (Mission Airbus - Customer Services)",
                "period": "Janv. 2023 - Nov. 2024",
            }
        ]
    }


def test_cv_parse_rejects_pdf_without_extractable_text(monkeypatch) -> None:
    monkeypatch.setattr(cv_parse_service, "_extract_text_from_pdf", lambda _: "")

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 422
    assert "text-based PDF" in response.json()["detail"]


def test_cv_parse_rejects_oversized_files() -> None:
    oversized_bytes = b"a" * (cv_parse_service.MAX_CV_FILE_SIZE_BYTES + 1)
    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(oversized_bytes), "application/pdf")},
    )

    assert response.status_code == 413
