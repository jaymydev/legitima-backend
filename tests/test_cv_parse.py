import io

from fastapi.testclient import TestClient
from PIL import Image
import pytesseract

from app.main import app
from app.api.routes import cv as cv_route
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


def test_cv_parse_extracts_experiences_from_image_ocr(monkeypatch) -> None:
    monkeypatch.setattr(
        cv_parse_service,
        "_extract_text_from_image",
        lambda _: """
        Experience
        PLM Engineer - Confidential Program | Jan 2026 - Present
        """,
    )

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.jpg", io.BytesIO(b"fake-image"), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "experiences": [
            {
                "title": "PLM Engineer",
                "company": "Confidential Program",
                "period": "Jan 2026 - Present",
            }
        ]
    }


def test_cv_parse_offloads_blocking_parser_to_threadpool(monkeypatch) -> None:
    calls = {}

    async def fake_run_in_threadpool(function, **kwargs):
        calls["function"] = function
        calls["kwargs"] = kwargs
        return cv_parse_service.CVParseResponse(
            experiences=[
                cv_parse_service.CVExperience(
                    title="Développeur logiciel",
                    company="Legitima",
                    period="2024",
                )
            ]
        )

    monkeypatch.setattr(cv_route, "run_in_threadpool", fake_run_in_threadpool)

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(b"fake-pdf"), "application/pdf")},
    )

    assert response.status_code == 200
    assert calls["function"] is cv_route.parse_cv_file
    assert calls["kwargs"]["content_type"] == "application/pdf"
    assert calls["kwargs"]["file_bytes"] == b"fake-pdf"
    assert isinstance(calls["kwargs"]["started_at"], float)


def test_cv_parse_downscales_large_images_before_ocr(monkeypatch) -> None:
    image_bytes = io.BytesIO()
    Image.new("RGB", (4000, 3000), "white").save(image_bytes, format="JPEG")
    observed = {}

    def fake_image_to_string(image, **kwargs):
        observed["size"] = image.size
        observed["timeout"] = kwargs["timeout"]
        observed["config"] = kwargs["config"]
        return "Experience\nDéveloppeur logiciel - 2024"

    monkeypatch.setattr(pytesseract, "image_to_string", fake_image_to_string)

    extracted_text = cv_parse_service._extract_text_from_image(image_bytes.getvalue())

    assert extracted_text == "Experience\nDéveloppeur logiciel - 2024"
    assert observed == {"size": (2400, 1800), "timeout": 20, "config": "--psm 3"}


def test_cv_parse_targets_main_column_for_sidebar_cv_layout(monkeypatch) -> None:
    image_bytes = io.BytesIO()
    image = Image.new("RGB", (1054, 1492), "white")
    for x in range(358):
        for y in range(1492):
            image.putpixel((x, y), (12, 41, 79))
    image.save(image_bytes, format="PNG")
    observed_calls = []

    def fake_image_to_string(image, **kwargs):
        observed_calls.append(
            {
                "size": image.size,
                "timeout": kwargs["timeout"],
                "config": kwargs["config"],
            }
        )
        return "EXPÉRIENCES PROFESSIONNELLES\nCOORDINATRICE D'EXPLOITATION - OCEA SMART BUILDING\nDepuis septembre 2020"

    monkeypatch.setattr(pytesseract, "image_to_string", fake_image_to_string)

    extracted_text = cv_parse_service._extract_text_from_image(image_bytes.getvalue())

    assert "COORDINATRICE D'EXPLOITATION" in extracted_text
    assert observed_calls == [
        {
            "size": (696, 1492),
            "timeout": 20,
            "config": "--psm 4",
        }
    ]


def test_cv_parse_falls_back_to_full_page_after_sidebar_timeout(monkeypatch) -> None:
    image_bytes = io.BytesIO()
    image = Image.new("RGB", (1054, 1492), "white")
    for x in range(358):
        for y in range(1492):
            image.putpixel((x, y), (12, 41, 79))
    image.save(image_bytes, format="PNG")
    observed_configs = []

    def fake_image_to_string(image, **kwargs):
        observed_configs.append(kwargs["config"])
        if kwargs["config"] == "--psm 4":
            raise RuntimeError("Tesseract process timeout")
        return "Experience\nPLM Engineer - Confidential Program | Jan 2026 - Present"

    monkeypatch.setattr(pytesseract, "image_to_string", fake_image_to_string)

    extracted_text = cv_parse_service._extract_text_from_image(image_bytes.getvalue())

    assert "PLM Engineer" in extracted_text
    assert observed_configs == ["--psm 4", "--psm 3"]


def test_cv_parse_sidebar_strategy_prevents_observed_422_to_500_regression(monkeypatch) -> None:
    image_bytes = io.BytesIO()
    image = Image.new("RGB", (1054, 1492), "white")
    for x in range(358):
        for y in range(1492):
            image.putpixel((x, y), (12, 41, 79))
    image.save(image_bytes, format="PNG")

    def fake_image_to_string(current_image, **kwargs):
        if kwargs["config"] == "--psm 4":
            return "EXPÉRIENCES PROFESSIONNELLES\nCOORDINATRICE D'EXPLOITATION - OCEA SMART BUILDING\nDepuis septembre 2020"
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_string", fake_image_to_string)

    extracted_text = cv_parse_service._extract_text_from_image(image_bytes.getvalue())
    parsed = cv_parse_service._response_from_extracted_text(extracted_text)

    assert parsed.model_dump() == {
        "experiences": [
            {
                "title": "COORDINATRICE D'EXPLOITATION",
                "company": "OCEA SMART BUILDING",
                "period": "Depuis septembre 2020",
            }
        ]
    }


def test_cv_parse_rejects_image_without_extractable_text(monkeypatch) -> None:
    monkeypatch.setattr(cv_parse_service, "_extract_text_from_image", lambda _: "")

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.png", io.BytesIO(b"fake-image"), "image/png")},
    )

    assert response.status_code == 422
    assert "No extractable text was found in the image" in response.json()["detail"]


def test_cv_parse_returns_500_when_ocr_engine_is_unavailable(monkeypatch) -> None:
    def raise_ocr_error(_: bytes) -> str:
        raise RuntimeError("OCR dependencies are not installed")

    monkeypatch.setattr(cv_parse_service, "_extract_text_from_image", raise_ocr_error)

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.png", io.BytesIO(b"fake-image"), "image/png")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "OCR dependencies are not installed"}


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
                "title": "Software Engineer",
                "company": "AI Internal Project (Capgemini)",
                "period": "2025",
            },
            {
                "title": "PLM Technical Consultant",
                "company": "Airbus (via Capgemini)",
                "period": "2024",
            },
            {
                "title": "Software & Test Engineer",
                "company": "Aerospace/Automotive Programs",
                "period": "2017-2023",
            },
        ]
    }


def test_cv_parse_handles_reference_cv_style_experience_blocks() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        COORDINATRICE D'EXPLOITATION - OCEA SMART BUILDING
        Depuis septembre 2020 - L'Union (31)
        MISSIONS PRINCIPALES
        ASSISTANTE ADMINISTRATIVE INDÉPENDANTE - AD 2 Assist'U - Brive-la-Gaillarde
        Depuis janvier 2020
        ASSISTANTE ADMINISTRATION DES VENTES - LESER Sarl - L'Union (31)
        Juillet 2014 - Juin 2017
        EMPLOYÉE ADMINISTRATIVE - TEN Sud-Ouest - Toulouse (31)
        Septembre 2012 - Juillet 2014
        TECHNICIENNE DE PAIE - OPTINERIS - Tulle (19)
        Mai 2018 - Octobre 2018 (CDD)
        FORMATIONS
        DUT GEA
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "COORDINATRICE D'EXPLOITATION",
                "company": "OCEA SMART BUILDING",
                "period": "Depuis septembre 2020",
            },
            {
                "title": "ASSISTANTE ADMINISTRATIVE INDÉPENDANTE",
                "company": "AD 2 Assist'U - Brive-la-Gaillarde",
                "period": "Depuis janvier 2020",
            },
            {
                "title": "TECHNICIENNE DE PAIE",
                "company": "OPTINERIS - Tulle (19)",
                "period": "Mai 2018 - Octobre 2018",
            },
            {
                "title": "ASSISTANTE ADMINISTRATION DES VENTES",
                "company": "LESER Sarl - L'Union (31)",
                "period": "Juillet 2014 - Juin 2017",
            },
            {
                "title": "EMPLOYÉE ADMINISTRATIVE",
                "company": "TEN Sud-Ouest - Toulouse (31)",
                "period": "Septembre 2012 - Juillet 2014",
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


def test_cv_parse_handles_title_company_then_period_lines_with_locations() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        COORDINATRICE D'EXPLOITATION - OCEA SMART BUILDING
        Depuis septembre 2020 - L'Union (31)
        Pilotage administratif et opérationnel des activités.
        ASSISTANTE ADMINISTRATION DES VENTES - LESER Sarl - L'Union (31)
        Juillet 2014 - Juin 2017
        Gestion des commandes, suivi clients, traitement administratif.
        EMPLOYÉE ADMINISTRATIVE - TFN Sud-Ouest - Toulouse (31)
        Septembre 2012 - Juillet 2014
        Support administratif, gestion des dossiers.
        TECHNICIENNE DE PAIE - OPTINERIS - Tulle (19)
        Mai 2018 - Octobre 2018 (CDD)
        Réalisation des travaux de paie.
        FORMATIONS
        PRINCE2 FOUNDATION
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "COORDINATRICE D'EXPLOITATION",
                "company": "OCEA SMART BUILDING",
                "period": "Depuis septembre 2020",
            },
            {
                "title": "TECHNICIENNE DE PAIE",
                "company": "OPTINERIS - Tulle (19)",
                "period": "Mai 2018 - Octobre 2018",
            },
            {
                "title": "ASSISTANTE ADMINISTRATION DES VENTES",
                "company": "LESER Sarl - L'Union (31)",
                "period": "Juillet 2014 - Juin 2017",
            },
            {
                "title": "EMPLOYÉE ADMINISTRATIVE",
                "company": "TFN Sud-Ouest - Toulouse (31)",
                "period": "Septembre 2012 - Juillet 2014",
            },
        ]
    }


def test_cv_parse_cleans_ocr_noise_and_reattaches_leading_month_fragment() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        + COORDINATRICE D'EXPLOITATION - OCEA SMART BUILDING
        Depuis septembre 2020
        AMBASSADRICE DES VALEURS - OCEA - 2022 - 2025
        + ASSISTANTE ADMINISTRATIVE INDÉPENDANTE - AD 2 Assist'U - Brive-la-Gaillarde
        Depuis janvier 2020
        © ASSISTANTE ADMINISTRATION DES VENTES - LESER Sarl - L'Union (31)
        Juillet 2014 - Juin 2017
        eptembre - © EMPLOYÉE ADMINISTRATIVE - TFN Sud-Ouest - Toulouse (31) - 2012 - Juillet 2014
        FORMATIONS
        PRINCE2 FOUNDATION
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "COORDINATRICE D'EXPLOITATION",
                "company": "OCEA SMART BUILDING",
                "period": "Depuis septembre 2020",
            },
            {
                "title": "ASSISTANTE ADMINISTRATIVE INDÉPENDANTE",
                "company": "AD 2 Assist'U - Brive-la-Gaillarde",
                "period": "Depuis janvier 2020",
            },
            {
                "title": "AMBASSADRICE DES VALEURS",
                "company": "OCEA",
                "period": "2022 - 2025",
            },
            {
                "title": "ASSISTANTE ADMINISTRATION DES VENTES",
                "company": "LESER Sarl - L'Union (31)",
                "period": "Juillet 2014 - Juin 2017",
            },
            {
                "title": "EMPLOYÉE ADMINISTRATIVE",
                "company": "TFN Sud-Ouest - Toulouse (31)",
                "period": "Septembre 2012 - Juillet 2014",
            },
        ]
    }


def test_cv_parse_reattaches_split_month_fragment_from_period_line() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        EMPLOYÉE ADMINISTRATIVE - TFN Sud-Ouest - Toulouse (31)
        eptembre 2012 - Juillet 2014
        FORMATIONS
        PRINCE2 FOUNDATION
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "EMPLOYÉE ADMINISTRATIVE",
                "company": "TFN Sud-Ouest - Toulouse (31)",
                "period": "Septembre 2012 - Juillet 2014",
            }
        ]
    }


def test_cv_parse_sorts_experiences_by_recency_instead_of_ocr_order() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        EMPLOYÉE ADMINISTRATIVE - TFN Sud-Ouest - Toulouse (31)
        Septembre 2012 - Juillet 2014
        TECHNICIENNE DE PAIE - OPTINERIS - Tulle (19)
        Mai 2018 - Octobre 2018 (CDD)
        FORMATIONS
        PRINCE2 FOUNDATION
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {
                "title": "TECHNICIENNE DE PAIE",
                "company": "OPTINERIS - Tulle (19)",
                "period": "Mai 2018 - Octobre 2018",
            },
            {
                "title": "EMPLOYÉE ADMINISTRATIVE",
                "company": "TFN Sud-Ouest - Toulouse (31)",
                "period": "Septembre 2012 - Juillet 2014",
            },
        ]
    }


def test_cv_parse_keeps_only_five_most_recent_experiences() -> None:
    result = cv_parse_service.parse_cv_text(
        """
        EXPÉRIENCES PROFESSIONNELLES
        EXP A - SOCIETE A
        2010 - 2011
        EXP B - SOCIETE B
        2012 - 2013
        EXP C - SOCIETE C
        2014 - 2015
        EXP D - SOCIETE D
        2016 - 2017
        EXP E - SOCIETE E
        2018 - 2019
        EXP F - SOCIETE F
        2020 - 2021
        FORMATIONS
        BTS
        """
    )

    assert result.model_dump() == {
        "experiences": [
            {"title": "EXP F", "company": "SOCIETE F", "period": "2020 - 2021"},
            {"title": "EXP E", "company": "SOCIETE E", "period": "2018 - 2019"},
            {"title": "EXP D", "company": "SOCIETE D", "period": "2016 - 2017"},
            {"title": "EXP C", "company": "SOCIETE C", "period": "2014 - 2015"},
            {"title": "EXP B", "company": "SOCIETE B", "period": "2012 - 2013"},
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


def test_cv_parse_rejects_pdf_without_exploitable_experiences(monkeypatch) -> None:
    monkeypatch.setattr(
        cv_parse_service,
        "_extract_text_from_pdf",
        lambda _: "This is a readable document, but it is not a CV.",
    )

    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 422
    assert "No exploitable professional experiences" in response.json()["detail"]


def test_cv_parse_rejects_oversized_files() -> None:
    oversized_bytes = b"a" * (cv_parse_service.MAX_CV_FILE_SIZE_BYTES + 1)
    response = TestClient(app).post(
        "/cv/parse",
        files={"file": ("resume.pdf", io.BytesIO(oversized_bytes), "application/pdf")},
    )

    assert response.status_code == 413
