import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import errors
from app.api.routes import interview_preparation as route
from app.services.interview_preparation import QUESTIONNAIRE_VERSION
from app.main import app


client = TestClient(app)


def _required_answers(use_case: dict) -> list[dict[str, str]]:
    return [
        {"question_id": question["id"], "answer": f"Réponse pour {question['id']}"}
        for question in use_case["questions"]
        if question["required"]
    ]


def test_catalog_exposes_six_distinct_versioned_use_cases() -> None:
    response = client.get("/v2/interview-preparation/use-cases")

    assert response.status_code == 200
    use_cases = response.json()["use_cases"]
    assert [item["id"] for item in use_cases] == [
        "recruitment",
        "internal_mobility",
        "role_evolution",
        "mid_year",
        "annual_review",
        "performance_review",
    ]
    assert all(
        item["questionnaire_version"] == QUESTIONNAIRE_VERSION for item in use_cases
    )
    assert len({question["id"] for item in use_cases for question in item["questions"]}) > 30
    assert all(
        question["options"] or question["suggestions"]
        for item in use_cases
        for question in item["questions"]
    )


def test_each_use_case_has_its_own_required_questions() -> None:
    use_cases = client.get("/v2/interview-preparation/use-cases").json()["use_cases"]
    required_sets = [
        frozenset(question["id"] for question in item["questions"] if question["required"])
        for item in use_cases
    ]

    assert len(set(required_sets)) == 6


def test_analyze_rejects_missing_required_answers() -> None:
    response = client.post(
        "/v2/interview-preparation/analyze",
        json={
            "use_case_id": "mid_year",
            "questionnaire_version": QUESTIONNAIRE_VERSION,
            "answers": [{"question_id": "role_context", "answer": "Responsable produit"}],
        },
    )

    assert response.status_code == 422
    # Which answers are missing is a client-contract detail: it goes to the log,
    # not to the person waiting on the screen.
    assert response.json()["code"] == errors.PREPARATION_INVALID_REQUEST
    assert "question_id" not in response.text


def test_analyze_rejects_stale_questionnaire_version() -> None:
    response = client.post(
        "/v2/interview-preparation/analyze",
        json={
            "use_case_id": "annual_review",
            "questionnaire_version": "0.9",
            "answers": [{"question_id": "role_scope", "answer": "Développement"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == errors.PREPARATION_INVALID_REQUEST


def test_analyze_returns_specialized_structured_preparation(monkeypatch) -> None:
    use_case = next(
        item
        for item in client.get("/v2/interview-preparation/use-cases").json()["use_cases"]
        if item["id"] == "performance_review"
    )
    model_response = {
        "use_case_id": "performance_review",
        "title": "Préparation de l’entretien de performance",
        "summary": "Une discussion factuelle appuyée sur les résultats disponibles.",
        "sections": [
            {
                "title": "Résultats et écarts",
                "content": "Présenter les résultats puis reconnaître clairement les écarts.",
            }
        ],
        "talking_points": ["Distinguer les faits du contexte."],
        "action_plan": ["Proposer un point de suivi mensuel."],
    }

    class FakeCompletions:
        def create(self, **kwargs):
            prompt = kwargs["messages"][0]["content"]
            assert "Entretien de performance" in prompt
            assert "Réponse pour measurable_results" in prompt
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(model_response, ensure_ascii=False))
                    )
                ]
            )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions())
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(route, "OpenAI", lambda api_key: fake_client)

    response = client.post(
        "/v2/interview-preparation/analyze",
        json={
            "use_case_id": use_case["id"],
            "questionnaire_version": use_case["questionnaire_version"],
            "answers": _required_answers(use_case),
        },
    )

    assert response.status_code == 200
    assert response.json() == model_response


def test_recruitment_uses_freemium_context_without_reasking_for_cv(monkeypatch) -> None:
    use_case = next(
        item
        for item in client.get("/v2/interview-preparation/use-cases").json()["use_cases"]
        if item["id"] == "recruitment"
    )
    question_ids = {question["id"] for question in use_case["questions"]}
    assert "target_role" not in question_ids
    assert "career_steps" not in question_ids
    assert "interview_stage" in question_ids
    assert "desired_takeaway" in question_ids

    model_response = {
        "use_case_id": "recruitment",
        "title": "Préparation de l’entretien",
        "summary": "Une candidature structurée et factuelle.",
        "sections": [{"title": "Pitch", "content": "Présentation synthétique."}],
        "talking_points": ["Relier les expériences au poste."],
        "action_plan": ["Relire les preuves avant l’entretien."],
    }

    class FakeCompletions:
        def create(self, **kwargs):
            prompt = kwargs["messages"][0]["content"]
            assert "Responsable produit" in prompt
            assert "Coordination de projets" in prompt
            assert "Fiche express" in prompt
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(model_response, ensure_ascii=False))
                    )
                ]
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        route,
        "OpenAI",
        lambda api_key: SimpleNamespace(
            chat=SimpleNamespace(completions=FakeCompletions())
        ),
    )

    answers = _required_answers(use_case)
    next(
        item for item in answers if item["question_id"] == "preparation_depth"
    )["answer"] = "Fiche express"

    response = client.post(
        "/v2/interview-preparation/analyze",
        json={
            "use_case_id": "recruitment",
            "questionnaire_version": use_case["questionnaire_version"],
            "answers": answers,
            "context": {
                "target_role": "Responsable produit",
                "career_experiences": "Coordination de projets",
                "sensitive_point": "Transition",
                "freemium_analysis": "Parcours cohérent",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == model_response


def test_analyze_does_not_log_answer_content(monkeypatch, caplog) -> None:
    use_case = next(
        item
        for item in client.get("/v2/interview-preparation/use-cases").json()["use_cases"]
        if item["id"] == "recruitment"
    )
    secret_marker = "CONTENU_CONFIDENTIEL_DU_TESTEUR"

    class FailingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("temporary failure")

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FailingCompletions())
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(route, "OpenAI", lambda api_key: fake_client)

    answers = _required_answers(use_case)
    answers[0]["answer"] = secret_marker
    response = client.post(
        "/v2/interview-preparation/analyze",
        json={
            "use_case_id": use_case["id"],
            "questionnaire_version": use_case["questionnaire_version"],
            "answers": answers,
            "context": {
                "career_experiences": secret_marker,
            },
        },
    )

    assert response.status_code == 500
    assert secret_marker not in caplog.text


def _kickoff_context() -> dict:
    return {
        "target_role": "Product Manager Senior",
        "career_experiences": "2019-2022 pilotage de projets techniques, 2022-2024 coordination produit, 2025 transition.",
        "sensitive_point": "Transition de six mois en 2025",
        "freemium_analysis": "Objection probable : pourquoi cette interruption en 2025 ?",
    }


def test_kickoff_returns_one_objection_and_its_answer(monkeypatch) -> None:
    model_response = {
        "objection": "Pourquoi cette interruption de six mois en 2025 ?",
        "defensible_answer": (
            "Cette période a été un repositionnement volontaire vers le produit. "
            "J'y ai consolidé ce que la coordination produit m'avait déjà appris."
        ),
    }

    class FakeCompletions:
        def create(self, **kwargs):
            prompt = kwargs["messages"][0]["content"]
            # The lean context must reach the prompt: that is the whole point
            # of the kickoff, which runs before any guided question.
            assert "Product Manager Senior" in prompt
            assert "Transition de six mois en 2025" in prompt
            # The model reliably filled the sensitive period with invented
            # activity ("je me suis forme", "j'ai suivi les tendances du
            # marche") until these were named as forbidden. A candidate who
            # repeats an invented activity is caught out on the follow-up
            # question, which is worse than not preparing at all.
            assert "INTERDICTION CENTRALE" in prompt
            assert "je me suis forme" in prompt.replace("\u00e9", "e")
            assert "TRAJECTOIRE" in prompt
            assert kwargs["response_format"] == {"type": "json_object"}
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(model_response, ensure_ascii=False))
                    )
                ]
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        route, "OpenAI", lambda api_key: SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    )

    response = client.post(
        "/v2/interview-preparation/kickoff",
        json={"context": _kickoff_context()},
    )

    assert response.status_code == 200
    assert response.json() == model_response


def test_kickoff_rejects_a_context_with_nothing_to_reason_from() -> None:
    response = client.post(
        "/v2/interview-preparation/kickoff",
        json={"context": {"sensitive_point": "Un trou de six mois"}},
    )

    # A sensitive point alone gives no career thread to answer from; inventing
    # one is exactly what the product must never do.
    assert response.status_code == 422


def test_kickoff_rejects_unknown_context_keys() -> None:
    context = _kickoff_context()
    context["unexpected_field"] = "valeur"

    response = client.post(
        "/v2/interview-preparation/kickoff",
        json={"context": context},
    )

    assert response.status_code == 422


def test_kickoff_does_not_log_context_content(monkeypatch, caplog) -> None:
    secret_marker = "CONTENU_CONFIDENTIEL_DU_TESTEUR"

    class FailingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("temporary failure")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        route, "OpenAI", lambda api_key: SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    )

    context = _kickoff_context()
    context["career_experiences"] = secret_marker
    response = client.post(
        "/v2/interview-preparation/kickoff",
        json={"context": context},
    )

    assert response.status_code == 500
    assert secret_marker not in caplog.text


def test_every_use_case_asks_what_the_person_fears() -> None:
    """The mechanism the product exists for must be solicited everywhere.

    Only recruitment used to ask it. The other five collected the meeting's
    agenda and returned it reformatted, never touching the sensitive point —
    measured at 92% of the user's own words coming straight back.
    """
    catalog = client.get("/v2/interview-preparation/use-cases").json()["use_cases"]
    assert len(catalog) == 6

    for use_case in catalog:
        required = [q for q in use_case["questions"] if q["required"]]
        feared = [
            q for q in required
            if any(word in q["title"].lower() for word in ("craignez", "redoutez", "réserve"))
        ]
        assert feared, f"{use_case['id']} ne demande pas ce que la personne redoute"
        # Free text: an objection cannot be picked from a list.
        assert not feared[0]["options"], f"{use_case['id']}: la question redoutée doit rester ouverte"
        assert feared[0]["suggestions"], f"{use_case['id']}: la question redoutée doit guider la réponse"


def test_both_generation_prompts_forbid_inventing_the_gap() -> None:
    """The prohibition must cover the paid flow, not only the kickoff.

    It was first added to `generate_kickoff` alone, and the guided preparation
    kept producing « cette phase de transition est une opportunité d'acquérir
    de nouvelles compétences » from a context that said no such thing.
    """
    import inspect

    from app.services import interview_preparation as service

    for func in (service.generate_kickoff, service.generate_preparation):
        source = inspect.getsource(func)
        assert "INTERDICTION CENTRALE" in source, f"{func.__name__} n'interdit pas l'invention"
        assert "TRAJECTOIRE" in source, f"{func.__name__} ne recadre pas sur la trajectoire"
        assert "je me suis form" in source, f"{func.__name__} ne nomme pas les formulations interdites"


def test_every_use_case_asks_for_a_defensible_answer() -> None:
    """Each generation prompt must carry the « récit → réponses » mechanism.

    The old focuses described the meeting ("créer un bilan annuel équilibré")
    rather than the work, which is why five of six produced a paraphrase.
    """
    from app.services.interview_preparation import USE_CASES

    for use_case_id, definition in USE_CASES.items():
        focus = definition.analysis_focus.lower()
        assert "défendable" in focus or "objections probables" in focus, (
            f"{use_case_id}: la consigne ne demande pas de réponse défendable"
        )
