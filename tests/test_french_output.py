"""The page must be in French, including the part the model writes.

The app is French only. On 4 September 2026 a real personalisation shipped an
"Avant d'entrer" plan written entirely in English — on screen and in the
exported PDF, which is the sheet someone carries into the room. The prompt
already said "réponds uniquement en français"; nothing checked that it had.

The three lines below are the ones that actually shipped. They are the test
data on purpose: a plausible invented sentence would not have caught the
second one, which contains no word from the marker list the legacy `/analyze`
route matches on.
"""

import json
from types import SimpleNamespace

from app.services import interview_questions as service
from app.services.question_bank import ACTION_PLANS

#: Verbatim from the generation captured on 4 September 2026.
SHIPPED_ENGLISH_PLAN = [
    "Revise the key points of your experience with reliability improvements.",
    "Think about specific examples when discussing team management.",
    "Familiarize yourself with the requirements related to REST APIs.",
]

FRENCH_QUESTIONS = [
    {
        "question": f"Quelle est votre expérience sur le sujet {index} ?",
        "intent": "Cerner ce que la personne a réellement fait.",
        "answer": "Citez un projet précis, puis le résultat obtenu.",
        "kind": "guidance",
    }
    for index in range(service.MIN_QUESTIONS)
]


def _payload(action_plan: list[str]) -> dict:
    return {
        "use_case_id": "recruitment",
        "title": "Préparation à un entretien de recrutement",
        "questions": FRENCH_QUESTIONS,
        "action_plan": action_plan,
    }


def _scripted_openai(payloads: list[dict], calls: list[dict]):
    """A client that answers each call with the next payload, last one repeating.

    Records every call so a test can assert how many generations were spent:
    a retry that never fires and a retry that loops are both defects.
    """

    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, *args, **kwargs):
            index = min(len(calls), len(payloads) - 1)
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=json.dumps(payloads[index], ensure_ascii=False)
                        )
                    )
                ]
            )

    return FakeOpenAI()


def _generate(payloads: list[dict]) -> tuple[service.PreparedInterview, list[dict]]:
    calls: list[dict] = []
    definition = service.get_use_case("recruitment")
    assert definition is not None
    prepared = service.generate_prepared_interview(
        _scripted_openai(payloads, calls),
        definition,
        {"job_offer": "Une annonce de développeur back-end."},
        [],
        "",
    )
    return prepared, calls


def test_a_plan_that_stays_english_falls_back_to_the_hand_written_one() -> None:
    """The model drifts twice; the person still gets French.

    The fallback is deterministic rather than a third attempt: the bank's plan
    for this interview type is written by hand, always exists, and is what the
    person would have had without personalising at all. Degrading towards it
    is degrading towards the known good.
    """
    prepared, calls = _generate([_payload(SHIPPED_ENGLISH_PLAN)])

    assert prepared.action_plan == ACTION_PLANS["recruitment"]
    # One retry was spent, and only one: drift must not loop.
    assert len(calls) == 2
    for line in prepared.action_plan:
        assert line not in SHIPPED_ENGLISH_PLAN


def test_a_second_attempt_is_made_before_giving_up_on_the_model() -> None:
    """Drift once, French on the retry: the model's own plan is kept.

    Falling straight back to the bank would throw away a plan the retry was
    about to get right, and the personalised plan is the one that knows what
    the person wrote.
    """
    french_plan = [
        "Relisez l'annonce : c'est d'elle que viendront les questions.",
        "Redites votre réalisation à voix haute, avec son résultat.",
    ]
    prepared, calls = _generate([_payload(SHIPPED_ENGLISH_PLAN), _payload(french_plan)])

    assert prepared.action_plan == french_plan
    # One generation and one retry, never a third. The grounding pass adds no
    # call here: these questions are all `guidance`, and it only runs on
    # first-person claims.
    assert len(calls) == 2


def test_a_french_plan_is_never_retried() -> None:
    """No drift, no extra call: the guard must not cost a generation to
    everyone in order to protect the rare drift."""
    french_plan = ["Relisez l'annonce une dernière fois avant d'entrer."]
    prepared, calls = _generate([_payload(french_plan)])

    assert prepared.action_plan == french_plan
    # The single generation, and nothing else.
    assert len(calls) == 1
