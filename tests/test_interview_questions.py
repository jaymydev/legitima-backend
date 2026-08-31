"""The pivot's contract: the interview type carries the preparation.

The property worth protecting is that a useful page exists even when the person
supplies almost nothing. The old flow refused to start without a career path;
this one must not acquire the same reflex by accident.
"""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import errors
from app.api.routes import interview_questions as route
from app.main import app
from app.services import interview_questions as service

client = TestClient(app)

VALID_RESPONSE = {
    "use_case_id": "performance_review",
    "title": "Votre entretien de performance",
    "questions": [
        {
            "question": f"Question {index} ?",
            "intent": "Ce que votre interlocuteur cherche.",
            "answer": "Nommez le projet concerné, puis le résultat obtenu.",
        }
        for index in range(service.MIN_QUESTIONS)
    ],
    "action_plan": ["Relire vos chiffres."],
}


def _fake_openai(payload: dict):
    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, *args, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
                    )
                ]
            )

    return FakeOpenAI


def test_the_catalog_lists_six_types_without_an_unsure_option() -> None:
    response = client.get("/v3/interview/use-cases")

    assert response.status_code == 200
    use_cases = response.json()["use_cases"]
    assert [case["id"] for case in use_cases] == [
        "recruitment",
        "internal_mobility",
        "role_evolution",
        "annual_review",
        "mid_year",
        "performance_review",
    ]
    # "Je ne sais pas encore" is gone on purpose: someone who cannot name their
    # interview is not who this is for.
    assert all(case["questionnaire_version"] == service.QUESTIONS_VERSION for case in use_cases)


def test_a_performance_review_needs_no_answer_at_all(monkeypatch) -> None:
    """The pivot's core promise, asserted rather than assumed.

    The previous flow answered 422 without a career path. This one must produce
    a page from the interview type alone.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(route, "OpenAI", _fake_openai(VALID_RESPONSE))

    response = client.post(
        "/v3/interview/questions",
        json={
            "use_case_id": "performance_review",
            "questionnaire_version": service.QUESTIONS_VERSION,
        },
        headers={"X-Forwarded-For": "198.51.100.61"},
    )

    assert response.status_code == 200
    assert len(response.json()["questions"]) >= service.MIN_QUESTIONS


def test_a_recruitment_still_needs_the_job_offer(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    response = client.post(
        "/v3/interview/questions",
        json={
            "use_case_id": "recruitment",
            "questionnaire_version": service.QUESTIONS_VERSION,
        },
        headers={"X-Forwarded-For": "198.51.100.62"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == errors.PREPARATION_INVALID_REQUEST
    assert "job_offer" not in response.text


def test_an_unknown_type_is_refused() -> None:
    response = client.post(
        "/v3/interview/questions",
        json={"use_case_id": "coffee_chat", "questionnaire_version": service.QUESTIONS_VERSION},
        headers={"X-Forwarded-For": "198.51.100.63"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == errors.UNKNOWN_USE_CASE


def test_an_oversized_cv_text_is_refused_before_any_token_is_spent(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    response = client.post(
        "/v3/interview/questions",
        json={
            "use_case_id": "performance_review",
            "questionnaire_version": service.QUESTIONS_VERSION,
            "cv_text": "a" * 12_001,
        },
        headers={"X-Forwarded-For": "198.51.100.66"},
    )

    assert response.status_code == 422


def test_a_stale_questionnaire_is_refused() -> None:
    response = client.post(
        "/v3/interview/questions",
        json={"use_case_id": "performance_review", "questionnaire_version": "0.9"},
        headers={"X-Forwarded-For": "198.51.100.64"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == errors.PREPARATION_INVALID_REQUEST


def test_a_missing_key_never_names_the_variable(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/v3/interview/questions",
        json={"use_case_id": "performance_review", "questionnaire_version": service.QUESTIONS_VERSION},
        headers={"X-Forwarded-For": "198.51.100.65"},
    )

    assert response.status_code == 500
    assert response.json()["code"] == errors.SERVICE_UNAVAILABLE
    assert "OPENAI_API_KEY" not in response.text


EXPERIENCES = [
    service.CVExperience(title=f"Poste {index}", company=f"Société {index}", period=f"20{10 + index}")
    for index in range(6)
]


def test_only_an_internal_move_reads_the_career_and_only_three_roles() -> None:
    """The one place the CV is allowed in, and how far.

    Sending experiences with an annual review must change nothing: the manager
    already knows the person's history, so replaying it is noise at best.
    """
    mobility = service.build_prompt(
        service.USE_CASES["internal_mobility"], {}, EXPERIENCES
    )
    assert "Poste 0" in mobility and "Poste 2" in mobility
    assert "Poste 3" not in mobility, "only the last three roles belong in an internal move"

    annual = service.build_prompt(service.USE_CASES["annual_review"], {}, EXPERIENCES)
    assert "Poste 0" not in annual


def test_a_recruitment_may_use_the_whole_cv() -> None:
    prompt = service.build_prompt(service.USE_CASES["recruitment"], {"job_offer": "x"}, EXPERIENCES)

    assert "Poste 5" in prompt


@pytest.mark.parametrize("use_case_id", sorted(service.USE_CASES))
def test_every_prompt_forbids_inventing_facts(use_case_id: str) -> None:
    """With less input, the model has more room to invent — so the rule matters
    more here than it did before, not less."""
    # Le prompt est retourné à la ligne pour rester lisible, donc les sondes
    # portent sur le texte à espaces normalisés : reformater le prompt ne doit
    # pas casser le test, en supprimer la règle doit le casser.
    prompt = " ".join(service.build_prompt(service.USE_CASES[use_case_id], {}, []).split())

    # Ce que l'offre réclame décrit le poste, pas le parcours de la personne.
    # Une vraie génération a produit « j'ai utilisé Jira » à partir d'une simple
    # exigence d'annonce : la distinction doit rester écrite noir sur blanc.
    assert "PAS ce que la personne a fait" in prompt
    assert "n'affirme jamais à la première personne" in prompt
    assert "COMMENT répondre" in prompt


def test_an_over_long_answer_is_cut_at_a_sentence_boundary() -> None:
    sentences = "Première phrase. " + "Phrase de remplissage assez longue. " * 30
    trimmed = service.trim_to_budget(sentences, max_characters=120)

    assert len(trimmed) <= 120
    assert trimmed.endswith(".")
    assert "Première phrase." in trimmed


def test_a_single_long_sentence_is_kept_whole() -> None:
    """Half a sentence is worse than a long one when it has to be said aloud."""
    sentence = "Une seule phrase très longue qui dépasse largement le budget fixé pour la page."
    trimmed = service.trim_to_budget(sentence, max_characters=20)

    assert trimmed == sentence


def test_the_page_is_bounded_by_the_code_not_by_the_prompt(monkeypatch) -> None:
    """Asking the model for brevity works most of the time; the page has to hold
    every time."""
    verbose = dict(VALID_RESPONSE)
    verbose["questions"] = [
        {**question, "answer": "Phrase interminable et redondante. " * 40}
        for question in VALID_RESPONSE["questions"]
    ]
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(route, "OpenAI", _fake_openai(verbose))

    response = client.post(
        "/v3/interview/questions",
        json={"use_case_id": "performance_review", "questionnaire_version": service.QUESTIONS_VERSION},
        headers={"X-Forwarded-For": "198.51.100.66"},
    )

    assert response.status_code == 200
    for question in response.json()["questions"]:
        assert len(question["answer"]) <= service.MAX_ANSWER_CHARACTERS


def test_the_intent_is_bounded_too(monkeypatch) -> None:
    """It sits between the question and the answer, so it is read on the way to
    the thing the reader came for. One line earns that place; three do not."""
    wordy = dict(VALID_RESPONSE)
    wordy["questions"] = [
        {
            **question,
            "intent": "Il cherche à mesurer votre lucidité. Puis votre capacité à "
            "structurer. Puis votre honnêteté sur les écarts constatés.",
        }
        for question in VALID_RESPONSE["questions"]
    ]
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(route, "OpenAI", _fake_openai(wordy))

    response = client.post(
        "/v3/interview/questions",
        json={"use_case_id": "performance_review", "questionnaire_version": service.QUESTIONS_VERSION},
        headers={"X-Forwarded-For": "198.51.100.67"},
    )

    assert response.status_code == 200
    for question in response.json()["questions"]:
        assert len(question["intent"]) <= service.MAX_INTENT_CHARACTERS
        assert question["intent"].endswith(".")


@pytest.mark.parametrize(
    "answer,claimed,expected",
    [
        ("J'ai piloté la refonte du site chez Novaweb.", "sentence", "sentence"),
        ("Mon équipe comptait huit personnes.", "sentence", "sentence"),
        # The model is optimistic about this field, and a directive labelled
        # "sentence" tells someone they have a line ready when they have
        # homework. They find out in the room.
        ("Citez un projet où vous avez cadré un besoin.", "sentence", "guidance"),
        ("Décrivez une situation tendue et votre approche.", "guidance", "guidance"),
    ],
)
def test_a_label_never_promises_more_than_the_answer_delivers(
    answer: str, claimed: str, expected: str
) -> None:
    assert service.settle_kind(answer, claimed) == expected


def test_only_a_recruitment_and_an_internal_move_read_the_cv_text() -> None:
    """The raw CV is material about the person, so the same rule applies to it
    as to the parsed rows: an annual review must not replay someone's history."""
    cv = "Refonte du site Ardal, equipe de 8 personnes, livree en 4 mois."

    assert cv in service.build_prompt(service.USE_CASES["recruitment"], {}, [], cv)
    assert cv in service.build_prompt(service.USE_CASES["internal_mobility"], {}, [], cv)
    assert cv not in service.build_prompt(service.USE_CASES["annual_review"], {}, [], cv)


def test_every_type_offers_a_way_to_earn_real_sentences() -> None:
    """Measured: with the job offer alone, one answer out of eight was a sentence
    someone could say; the rest were directives. Each type therefore carries at
    least one optional question whose whole purpose is to supply material.

    Annual and mid-year already ask for objectives, which is that material.
    """
    for use_case_id, definition in service.USE_CASES.items():
        optional = [q for q in definition.catalog.questions if not q.required]
        objectives = [q for q in definition.catalog.questions if "objectives" in q.id]
        assert optional or objectives, f"{use_case_id} has no way to earn a real answer"


@pytest.mark.parametrize(
    "answer,kind,checked",
    [
        ("J'ai piloté la refonte chez Novaweb.", "sentence", True),
        # The hole this closes: the model labelled a first-person claim as
        # guidance, so nothing verified it.
        ("Je privilégie la communication ouverte avec mes clients.", "guidance", True),
        ("Citez un projet et dites ce que vous avez livré.", "guidance", False),
    ],
)
def test_anything_that_asserts_gets_verified(answer: str, kind: str, checked: bool) -> None:
    question = service.PreparedQuestion(
        question="Q ?", intent="I.", answer=answer, kind=kind
    )
    assert service.needs_grounding(question) is checked
