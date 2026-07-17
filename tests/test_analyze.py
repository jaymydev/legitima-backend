import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import analyze as analyze_route


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


def test_analyze_rejects_unsupported_language() -> None:
    client = TestClient(app)
    payload = {
        "input": {
            "meta": {
                "version": "1.0",
                "language": "en",
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
    assert response.status_code == 422
    assert "Only French output is currently supported for /analyze" in json.dumps(response.json())


def test_analyze_retries_when_first_response_is_not_french(monkeypatch) -> None:
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
                "current_positioning": "Ingenieure logicielle",
                "evolution_logic": "Periodes de bench a requalifier",
            },
        }
    }

    english_response = {
        "analysis": {
            "strategic_reading": "Strong technical profile.",
            "dominant_competencies": "Backend engineering and leadership.",
            "career_logic": "Career progression toward technical leadership.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Bench periods.",
            "strategic_reinterpretation": "Time used for learning.",
            "rational_reframing": "A technical consolidation phase.",
        },
        "narrative": {
            "core_thread": "A technical path toward broader impact.",
            "positioning_statement": "A senior technical candidate.",
        },
        "interview_preparation": {
            "probable_objections": "Concerns about stability.",
            "structured_answers": "Explain skill progression.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Proven adaptability.",
            "final_alignment_statement": "Aligned with the target role.",
        },
    }
    french_response = {
        "analysis": {
            "strategic_reading": "Profil technique solide et cohérent.",
            "dominant_competencies": "Développement backend et coordination technique.",
            "career_logic": "Progression vers un rôle technique plus transverse.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Périodes de bench.",
            "strategic_reinterpretation": "Temps utilisé pour consolider les compétences.",
            "rational_reframing": "Phase de consolidation technique.",
        },
        "narrative": {
            "core_thread": "Un parcours technique qui gagne en impact.",
            "positioning_statement": "Profil technique senior crédible pour le poste visé.",
        },
        "interview_preparation": {
            "probable_objections": "Questionnement sur la stabilité du parcours.",
            "structured_answers": "Recentrer la réponse sur l'apprentissage et la cohérence.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Adaptabilité et progression constante.",
            "final_alignment_statement": "Le parcours est cohérent avec le rôle cible.",
        },
    }

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            content = english_response if self.calls == 1 else french_response
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))]
            )

    fake_client = FakeOpenAI(api_key="test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(analyze_route, "OpenAI", lambda api_key: fake_client)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json()["analysis"]["strategic_reading"] == "Profil technique solide et cohérent."
    assert fake_client.calls == 2


def test_analyze_returns_error_when_openai_call_fails(monkeypatch) -> None:
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
                "current_positioning": "Ingenieure logicielle",
                "evolution_logic": "Periodes de bench a requalifier",
            },
        }
    }

    class FailingOpenAI:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            raise RuntimeError("upstream unavailable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(analyze_route, "OpenAI", FailingOpenAI)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 500
    assert "OpenAI API call failed: upstream unavailable" == response.json()["detail"]


def test_analyze_returns_error_when_french_requirement_still_fails_after_retry(monkeypatch) -> None:
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
                "current_positioning": "Ingenieure logicielle",
                "evolution_logic": "Periodes de bench a requalifier",
            },
        }
    }

    english_response = {
        "analysis": {
            "strategic_reading": "Strong technical profile.",
            "dominant_competencies": "Backend engineering and leadership.",
            "career_logic": "Career progression toward technical leadership.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Bench periods.",
            "strategic_reinterpretation": "Time used for learning.",
            "rational_reframing": "A technical consolidation phase.",
        },
        "narrative": {
            "core_thread": "A technical path toward broader impact.",
            "positioning_statement": "A senior technical candidate.",
        },
        "interview_preparation": {
            "probable_objections": "Concerns about stability.",
            "structured_answers": "Explain skill progression.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Proven adaptability.",
            "final_alignment_statement": "Aligned with the target role.",
        },
    }

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(english_response)))]
            )

    fake_client = FakeOpenAI(api_key="test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(analyze_route, "OpenAI", lambda api_key: fake_client)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Model response did not satisfy the analyze quality requirements"
    }
    assert fake_client.calls == 2


def test_analyze_retries_when_response_contains_missing_accents(monkeypatch) -> None:
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
                "current_positioning": "Developpeur backend",
                "evolution_logic": "Progression vers plus de leadership",
            },
        }
    }

    accentless_response = {
        "analysis": {
            "strategic_reading": "Developpeur experimente avec une forte capacite de leadership.",
            "dominant_competencies": "Developpement backend et coordination technique.",
            "career_logic": "Progression coherente vers un role plus transverse.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Periodes de bench.",
            "strategic_reinterpretation": "Temps utilise pour consolider les competences.",
            "rational_reframing": "Phase de consolidation technique.",
        },
        "narrative": {
            "core_thread": "Un parcours technique qui gagne en impact.",
            "positioning_statement": "Profil technique senior credible pour le poste vise.",
        },
        "interview_preparation": {
            "probable_objections": "Questionnement sur la stabilite du parcours.",
            "structured_answers": "Recentrer la reponse sur l'apprentissage et la coherence.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Adaptabilite et progression constante.",
            "final_alignment_statement": "Le parcours est coherent avec le role cible.",
        },
    }
    corrected_response = {
        "analysis": {
            "strategic_reading": "Développeur expérimenté avec une forte capacité de leadership.",
            "dominant_competencies": "Développement backend et coordination technique.",
            "career_logic": "Progression cohérente vers un rôle plus transverse.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Périodes de bench.",
            "strategic_reinterpretation": "Temps utilisé pour consolider les compétences.",
            "rational_reframing": "Phase de consolidation technique.",
        },
        "narrative": {
            "core_thread": "Un parcours technique qui gagne en impact.",
            "positioning_statement": "Profil technique senior crédible pour le poste visé.",
        },
        "interview_preparation": {
            "probable_objections": "Questionnement sur la stabilité du parcours.",
            "structured_answers": "Recentrer la réponse sur l'apprentissage et la cohérence.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Adaptabilité et progression constante.",
            "final_alignment_statement": "Le parcours est cohérent avec le rôle cible.",
        },
    }

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            content = accentless_response if self.calls == 1 else corrected_response
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))]
            )

    fake_client = FakeOpenAI(api_key="test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(analyze_route, "OpenAI", lambda api_key: fake_client)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json()["analysis"]["strategic_reading"] == corrected_response["analysis"]["strategic_reading"]
    assert fake_client.calls == 2


def test_analyze_retries_when_response_duplicates_content(monkeypatch) -> None:
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
                "current_positioning": "Developpeur backend",
                "evolution_logic": "Progression vers plus de leadership",
            },
        }
    }

    duplicated_text = "Développeur expérimenté avec une forte capacité de leadership."
    duplicated_response = {
        "analysis": {
            "strategic_reading": duplicated_text,
            "dominant_competencies": "Développement backend et coordination technique.",
            "career_logic": "Progression cohérente vers un rôle plus transverse.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Périodes de bench.",
            "strategic_reinterpretation": "Temps utilisé pour consolider les compétences.",
            "rational_reframing": "Phase de consolidation technique.",
        },
        "narrative": {
            "core_thread": "Un parcours technique qui gagne en impact.",
            "positioning_statement": duplicated_text,
        },
        "interview_preparation": {
            "probable_objections": "Questionnement sur la stabilité du parcours.",
            "structured_answers": "Recentrer la réponse sur l'apprentissage et la cohérence.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Adaptabilité et progression constante.",
            "final_alignment_statement": "Le parcours est cohérent avec le rôle cible.",
        },
    }
    corrected_response = {
        "analysis": {
            "strategic_reading": "Développeur expérimenté avec une forte capacité à structurer des solutions robustes.",
            "dominant_competencies": "Développement backend et coordination technique.",
            "career_logic": "Progression cohérente vers un rôle plus transverse.",
        },
        "sensitive_reframing": {
            "identified_fragilities": "Périodes de bench.",
            "strategic_reinterpretation": "Temps utilisé pour consolider les compétences.",
            "rational_reframing": "Phase de consolidation technique.",
        },
        "narrative": {
            "core_thread": "Un parcours technique qui gagne en impact en prenant davantage de responsabilités.",
            "positioning_statement": "Profil technique senior crédible pour le poste visé.",
        },
        "interview_preparation": {
            "probable_objections": "Questionnement sur la stabilité du parcours.",
            "structured_answers": "Recentrer la réponse sur l'apprentissage et la cohérence.",
        },
        "legitimacy_anchor": {
            "objective_strength": "Adaptabilité et progression constante.",
            "final_alignment_statement": "Le parcours est cohérent avec le rôle cible.",
        },
    }

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            content = duplicated_response if self.calls == 1 else corrected_response
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))]
            )

    fake_client = FakeOpenAI(api_key="test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(analyze_route, "OpenAI", lambda api_key: fake_client)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json()["narrative"]["positioning_statement"] == corrected_response["narrative"]["positioning_statement"]
    assert fake_client.calls == 2
