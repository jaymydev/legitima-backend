"""Generate the questions someone will be asked, and answers they can give.

The product used to start from a career path: the user typed their history, an
LLM read it, and the interview type arrived last. It now starts from the
interview type, and the career path is optional material rather than the
subject. So this module does not analyse anyone — it prepares the exchange.

Two constraints shape everything here and they pull against each other. The
coverage must be wide, because the point is not to be surprised in the room.
The delivered page must be readable in five minutes, because that is when it
gets read: in the corridor, before going in. Wide coverage, short delivery —
the reconciliation is a small number of the *most likely* questions, each with
an answer short enough to say out loud, and never a long document.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from app.observability.logging import logger
from app.services.interview_preparation import InterviewQuestion, InterviewUseCase

INTERVIEW_QUESTIONS_MODEL = "gpt-4o-mini"

#: Bumped whenever the questionnaires below change shape. A client holding a
#: draft against an older version is asked to start again rather than to submit
#: answers to questions that no longer exist.
QUESTIONS_VERSION = "2.1"

#: What fits on one page, and therefore in five minutes.
MIN_QUESTIONS = 5
MAX_QUESTIONS = 8
MAX_ANSWER_CHARACTERS = 420
#: `intent` sits between the question and the answer, so it is read on the way
#: to the thing the reader actually came for. One short line earns that place;
#: two do not.
MAX_INTENT_CHARACTERS = 80
MAX_ACTION_PLAN_ITEMS = 3


class PreparedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    #: What the person across the table is actually checking. One sentence.
    #: This is what turns a script into something the reader can improvise from.
    intent: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    #: Whether `answer` is a sentence to say, or a directive on how to answer.
    #: Defaults to the modest one: a label that over-promises is worse than a
    #: label that under-promises, because the reader plans around it.
    kind: Literal["sentence", "guidance"] = "guidance"


class PreparedInterview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    title: str = Field(min_length=1)
    questions: list[PreparedQuestion] = Field(min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)
    action_plan: list[str] = Field(min_length=1, max_length=MAX_ACTION_PLAN_ITEMS)


class QuestionnaireAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    answer: str


class CVExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    company: str = ""
    period: str = ""


class PreparedInterviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    questionnaire_version: str
    answers: list[QuestionnaireAnswer] = Field(default_factory=list)
    #: Only two use cases read this, and they read it differently — the whole CV
    #: for a recruitment, the last three roles for an internal move. Sent by the
    #: client because the parsing already happens there via /cv/parse.
    experiences: list[CVExperience] = Field(default_factory=list)
    #: The CV as extracted text, before /cv/parse reduced it to rows.
    #:
    #: Measured: three rows of title/company/period answer "who are you" and
    #: nothing else, so seven answers out of eight stayed directives. The bullets
    #: the reduction throws away — "refonte du site X, équipe de 8" — are exactly
    #: the material the answers need.
    #:
    #: Bounded above what /cv/parse ever returns (MAX_RAW_TEXT_CHARACTERS): this
    #: field goes verbatim into a token-costing prompt on an unauthenticated
    #: route, so the honest client's cap cannot be the only one.
    cv_text: str = Field(default="", max_length=12000)


@dataclass(frozen=True)
class UseCaseDefinition:
    catalog: InterviewUseCase
    #: What this interview is really testing. Goes into the prompt verbatim.
    focus: str
    #: How many of the supplied experiences the prompt may use, if any.
    experience_limit: int = 0


def _question(
    question_id: str,
    title: str,
    helper: str,
    *,
    required: bool = True,
    input_type: str = "long_text",
) -> InterviewQuestion:
    return InterviewQuestion(
        id=question_id,
        title=title,
        helper=helper,
        required=required,
        input_type=input_type,
    )


USE_CASES: dict[str, UseCaseDefinition] = {
    "recruitment": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="recruitment",
            title="Entretien de recrutement",
            short_title="Recrutement",
            description="En face, un recruteur ou un manager qui cherche à savoir si vous tenez le poste.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question(
                    "job_offer",
                    "Collez l'offre d'emploi",
                    "Copiez le texte de l'annonce. Les questions seront tirées de ce qui y est demandé.",
                ),
                _question(
                    "achievement",
                    "Racontez une réalisation proche de ce poste",
                    "Une situation, ce que vous avez fait, ce que ça a donné. C'est elle qui transforme les consignes en phrases que vous pourrez dire.",
                    required=False,
                ),
            ],
        ),
        focus=(
            "Le recruteur vérifie l'adéquation au poste décrit dans l'annonce. "
            "Tire les questions des exigences réellement écrites dans l'offre, "
            "pas de généralités sur le métier."
        ),
        experience_limit=10,
    ),
    "internal_mobility": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="internal_mobility",
            title="Entretien de mobilité interne",
            short_title="Mobilité interne",
            description="On vous demandera pourquoi vous partez autant que pourquoi vous arrivez.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question("current_role", "Votre poste actuel", "Intitulé et mission principale.", input_type="short_text"),
                _question("current_site", "Où êtes-vous aujourd'hui ?", "Site, ville ou entité.", input_type="short_text"),
                _question("target_role", "Le poste visé", "Intitulé et équipe.", input_type="short_text"),
                _question("target_site", "Où voulez-vous aller ?", "Site, ville ou entité visée.", input_type="short_text"),
                _question(
                    "current_achievement",
                    "Qu'avez-vous accompli dans votre poste actuel ?",
                    "Un résultat concret, même modeste. Sans lui, les réponses resteront des consignes.",
                    required=False,
                ),
            ],
        ),
        focus=(
            "Une mobilité interne se juge sur deux fronts à la fois : ce que le "
            "départ coûte à l'équipe actuelle, et ce que l'arrivée apporte à "
            "l'équipe visée. Traite les deux."
        ),
        experience_limit=3,
    ),
    "role_evolution": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="role_evolution",
            title="Entretien d'évolution de poste",
            short_title="Évolution de poste",
            description="Il faudra montrer que vous faites déjà une partie du poste visé.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question(
                    "target_position",
                    "Le poste que vous visez",
                    "Le niveau ou les responsabilités souhaités, et ce qui changerait dans votre rôle.",
                ),
                _question(
                    "already_doing",
                    "Que faites-vous déjà du poste visé ?",
                    "Les responsabilités que vous exercez sans qu'elles figurent dans votre fiche de poste.",
                    required=False,
                ),
            ],
        ),
        focus=(
            "Une évolution ne s'accorde pas sur un potentiel mais sur des "
            "responsabilités déjà exercées. Les questions doivent chercher la "
            "preuve que le poste est déjà tenu en partie."
        ),
    ),
    "annual_review": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="annual_review",
            title="Entretien annuel",
            short_title="Annuel",
            description="Votre manager connaît déjà votre parcours : ce sont vos résultats qui se discutent.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question(
                    "year_objectives",
                    "Vos objectifs de l'année",
                    "Ce qui vous avait été fixé, et où vous en êtes. C'est ce qui rend le discours vraiment vôtre.",
                ),
            ],
        ),
        focus=(
            "Votre interlocuteur connaît déjà le parcours : n'explique jamais "
            "d'où vient la personne. L'entretien porte sur les résultats de "
            "l'année et sur ce qui vient ensuite."
        ),
    ),
    "mid_year": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="mid_year",
            title="Entretien de mi-année",
            short_title="Mi-année",
            description="Le point d'étape, quand il est encore temps d'ajuster les objectifs.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question(
                    "midyear_objectives",
                    "Vos objectifs de mi-année",
                    "Ce qui était prévu et où vous en êtes à mi-parcours.",
                ),
            ],
        ),
        focus=(
            "Un point de mi-année sert à corriger la trajectoire pendant qu'il "
            "en est encore temps. Les questions doivent ouvrir sur des "
            "ajustements, pas sur un bilan définitif."
        ),
    ),
    "performance_review": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="performance_review",
            title="Entretien de performance",
            short_title="Performance",
            description="Votre travail est évalué : chaque affirmation doit pouvoir être étayée.",
            questionnaire_version=QUESTIONS_VERSION,
            questions=[
                _question(
                    "result_to_highlight",
                    "Quel résultat voulez-vous mettre en avant ?",
                    "Le fait que vous voulez qu'on retienne, avec ce qui permet de l'étayer.",
                    required=False,
                ),
            ],
        ),
        focus=(
            "Une évaluation de performance a des conséquences. Chaque réponse "
            "doit pouvoir être étayée, et aucune ne doit promettre ce qui n'est "
            "pas tenable."
        ),
    ),
}


def list_use_cases() -> list[InterviewUseCase]:
    return [definition.catalog for definition in USE_CASES.values()]


def get_use_case(use_case_id: str) -> UseCaseDefinition | None:
    return USE_CASES.get(use_case_id)


def validate_request(
    payload: PreparedInterviewRequest,
    definition: UseCaseDefinition,
) -> dict[str, str]:
    """Check the answers against the questionnaire, and return them by id.

    Unlike the previous flow, most answers here are optional: the interview type
    alone is enough to prepare something useful, and refusing to answer until a
    form is full is exactly what this pivot removes.
    """
    if payload.questionnaire_version != QUESTIONS_VERSION:
        raise ValueError("Questionnaire version is no longer supported")

    known_ids = {question.id for question in definition.catalog.questions}
    answers: dict[str, str] = {}
    for item in payload.answers:
        if item.question_id not in known_ids:
            raise ValueError(f"Unknown question_id: {item.question_id}")
        if item.question_id in answers:
            raise ValueError(f"Duplicate question_id: {item.question_id}")
        answers[item.question_id] = item.answer.strip()

    missing = [
        question.id
        for question in definition.catalog.questions
        if question.required and not answers.get(question.id)
    ]
    if missing:
        raise ValueError(f"Missing required answers: {', '.join(missing)}")

    return answers


_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
#: Enough to tell a sentence someone says from a directive telling them how.
_FIRST_PERSON = re.compile(r"\b(je|mon|ma|mes)\b|\bj\u2019|\bj\'", re.IGNORECASE)


def settle_kind(answer: str, claimed: str) -> str:
    """Never let the label promise more than the answer delivers.

    The model decides `kind`, and it is optimistic about it. A directive
    labelled "sentence" tells someone they have a line ready when they have
    homework — and they find out in the room. Downgrading only ever goes one
    way, so the label is safe to plan around.
    """
    if claimed == "sentence" and not _FIRST_PERSON.search(answer):
        return "guidance"
    return claimed


def trim_to_budget(text: str, max_characters: int = MAX_ANSWER_CHARACTERS) -> str:
    """Cut an over-long answer at a sentence boundary.

    Asking the model for brevity works most of the time; the page has to hold
    every time. Cutting mid-sentence would hand someone half a sentence to say
    out loud, so a whole sentence is dropped instead. The first sentence is kept
    whatever its length — a truncated answer is worse than a long one.
    """
    cleaned = text.strip()
    if len(cleaned) <= max_characters:
        return cleaned

    kept: list[str] = []
    for sentence in _SENTENCE_END.split(cleaned):
        candidate = " ".join(kept + [sentence])
        if kept and len(candidate) > max_characters:
            break
        kept.append(sentence)
    return " ".join(kept).strip()


def build_prompt(
    definition: UseCaseDefinition,
    answers: dict[str, str],
    experiences: list[CVExperience],
    cv_text: str = "",
) -> str:
    usable = experiences[: definition.experience_limit] if definition.experience_limit else []
    cv_text = cv_text.strip() if definition.experience_limit else ""
    return f"""
Tu prépares quelqu'un à un entretien : {definition.catalog.title}.

Ce que cet entretien teste réellement :
{definition.focus}

TA TÂCHE
Produis les questions qui ont le plus de chances d'être posées, et pour chacune
une réponse que la personne peut dire à voix haute. Couvre large : le but est
qu'aucune question de l'entretien ne soit une surprise. Entre {MIN_QUESTIONS} et
{MAX_QUESTIONS} questions, les plus probables d'abord.

LA CONTRAINTE QUI PRIME
Cette page sera lue cinq minutes avant d'entrer. Chaque réponse tient en deux ou
trois phrases, dites à la première personne, prononçables telles quelles. Une
réponse courte et sûre vaut mieux qu'une réponse complète et impossible à
retenir.

CE QUE TU NE DOIS JAMAIS FAIRE
Deux sources arrivent plus bas et elles n'ont pas le même statut.

Ce que l'OFFRE ou le POSTE réclame décrit ce qu'on attend, PAS ce que la
personne a fait. Une exigence lue dans une annonce n'est jamais une information
sur son parcours. Transformer « maîtrise de Jira » en « j'ai utilisé Jira pour
suivre l'avancement » est l'erreur la plus grave que tu puisses commettre ici :
la personne récite une compétence qu'elle n'a peut-être pas, et se fait prendre
à la question suivante.

Seul CE QUE LA PERSONNE A ÉCRIT est un fait sur elle.

Donc : n'affirme jamais à la première personne une expérience, un outil, une
méthode, un chiffre ou un niveau qui ne soit pas écrit noir sur blanc dans ce
qu'elle a fourni.

CE QUE TU DOIS FAIRE DE CE QU'ELLE A ÉCRIT
Cette règle compte autant que la précédente. Ne pas inventer ne veut pas dire
ne rien affirmer : tout ce que la personne a écrit, tu dois t'en servir.

Une seule situation racontée nourrit souvent quatre ou cinq réponses — le même
projet éclaire le cadrage, le planning, la coordination et la gestion d'un
client difficile. Cherche activement, pour chaque question, ce qui dans sa
matière peut y répondre, même de biais.

Quand tu trouves : écris la phrase qu'elle dira, à la première personne, en
reprenant ses faits, ses chiffres et ses noms. `kind` vaut "sentence".
Exemple — matière fournie : « refonte reprise avec trois mois de retard, périmètre
recadré, deux fonctionnalités coupées, livré dans les délais révisés à 8 ».
Réponse attendue : « J'ai repris une refonte qui avait trois mois de retard.
J'ai recadré le périmètre avec le client et coupé deux fonctionnalités
secondaires, et nous avons livré dans les délais révisés à huit. »

Quand tu ne trouves rien : la réponse dit COMMENT répondre, à l'impératif, sans
rien affirmer — « Citez un projet où vous avez cadré un besoin, dites avec qui
vous l'avez fait, puis ce que vous avez livré » — et `kind` vaut "guidance".

Rendre une consigne alors que la matière existait est un échec au même titre
qu'inventer. Dans les deux cas la personne se retrouve sans phrase à dire.

Une réponse inventée met la personne en difficulté ; une consigne ne la met
jamais en défaut. N'oblige jamais quelqu'un à parler de ce qu'il ne maîtrise
pas, et ne lui fais jamais dire qu'il maîtrise quelque chose.

RÈGLES
- réponds uniquement en français ;
- reste professionnel, factuel et non-jugeant ;
- corrige-toi : relis chaque réponse et supprime toute affirmation dont la
  source n'est pas explicitement dans ce que la personne a écrit ;
- chaque phrase doit être grammaticalement complète ;
- deux questions ne doivent pas se recouvrir : si deux réponses se ressemblent,
  supprime-en une et propose autre chose ;
- `intent` dit ce que l'interlocuteur cherche derrière la question — c'est ce
  qui permet d'improviser si elle est posée autrement. UNE SEULE phrase, moins
  de {MAX_INTENT_CHARACTERS} caractères : elle est lue en passant, entre la
  question et la réponse ;
- `action_plan` : au plus {MAX_ACTION_PLAN_ITEMS} gestes concrets à faire avant
  d'entrer, jamais un résumé de ce qui précède.

Retourne uniquement un objet JSON respectant exactement cette structure :
{{
  "use_case_id": "{definition.catalog.id}",
  "title": "",
  "questions": [{{"question": "", "intent": "", "answer": "", "kind": "sentence|guidance"}}],
  "action_plan": [""]
}}

CE QUE LA PERSONNE A ÉCRIT — la seule source de faits sur elle.
Peut être vide ; dans ce cas aucune réponse ne doit rien affirmer d'elle.
{json.dumps(answers, ensure_ascii=False)}

EXPÉRIENCES PROFESSIONNELLES FOURNIES — faits sur elle, peuvent être vides.
{json.dumps([item.model_dump() for item in usable], ensure_ascii=False)}

CV DE LA PERSONNE, TEXTE BRUT — faits sur elle, peut être vide.
{cv_text}
"""


class _GroundingVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    grounded: bool
    #: The rewrite, only when `grounded` is false.
    answer: str = ""


class _GroundingReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdicts: list[_GroundingVerdict] = Field(default_factory=list)


def needs_grounding(question: PreparedQuestion) -> bool:
    """Whether this answer asserts something, whatever it is labelled.

    Checking only what the model called a "sentence" left a hole: it labelled
    "Je privilégie la communication ouverte et écoute les préoccupations des
    clients" as guidance, so nothing checked it — and it is a first-person claim
    about someone who never said it. What matters is whether the text asserts,
    not what the text is called.
    """
    return question.kind == "sentence" or bool(_FIRST_PERSON.search(question.answer))


def build_grounding_prompt(material: str, prepared: PreparedInterview) -> str:
    claims = [
        {"index": index, "answer": question.answer}
        for index, question in enumerate(prepared.questions)
        if needs_grounding(question)
    ]
    return f"""
Tu vérifies des réponses d'entretien écrites à la première personne.

VOICI TOUT CE QUE LA PERSONNE A ÉCRIT SUR ELLE :
{material}

Rien d'autre n'est vrai d'elle. En particulier, une exigence lue dans une offre
d'emploi — « anglais apprécié », « maîtrise de Jira » — décrit le poste, PAS son
parcours : une réponse qui l'affirme n'est pas appuyée.

Pour chaque réponse ci-dessous, dis si TOUT ce qu'elle affirme est appuyé par la
matière ci-dessus.

- appuyée : "grounded": true, et laisse "answer" vide ;
- non appuyée, même partiellement : "grounded": false, et réécris-la à
  l'impératif, sans rien affirmer, en gardant le sujet — par exemple
  « Citez un projet où vous avez tenu un budget, dites comment vous l'avez suivi. »

Une réponse partiellement appuyée est non appuyée : il suffit d'une affirmation
de trop pour que la personne soit prise en défaut.

Réponds uniquement par un objet JSON :
{{"verdicts": [{{"index": 0, "grounded": true, "answer": ""}}]}}

RÉPONSES À VÉRIFIER :
{json.dumps(claims, ensure_ascii=False)}
"""


def verify_grounding(
    client: OpenAI,
    material: str,
    prepared: PreparedInterview,
) -> PreparedInterview:
    """Second pass: keep only the first-person claims the material supports.

    Prompt wording alone proved unstable. Tightening it produced eight
    directives and no usable sentence; loosening it produced five sentences and
    three inventions — including "je suis à l'aise en anglais professionnel",
    read straight off an offer that merely listed English as a plus. The
    seesaw is the signal: one instruction cannot both authorise and forbid the
    same move reliably, so the check is a separate pass with one job.

    It only ever downgrades. A failure here leaves the generation untouched
    rather than dropping the page.
    """
    if not any(needs_grounding(question) for question in prepared.questions):
        return prepared

    try:
        completion = client.chat.completions.create(
            model=INTERVIEW_QUESTIONS_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": build_grounding_prompt(material, prepared)}
            ],
        )
        content = completion.choices[0].message.content if completion.choices else None
        if not content:
            return prepared
        report = _GroundingReport.model_validate_json(content)
    except Exception:
        logger.warning("Grounding pass failed, keeping the generation as written")
        return prepared

    corrections = {
        verdict.index: verdict
        for verdict in report.verdicts
        if not verdict.grounded
    }
    if not corrections:
        return prepared

    logger.info("Grounding pass downgraded %d unsupported answer(s)", len(corrections))
    questions = []
    for index, question in enumerate(prepared.questions):
        verdict = corrections.get(index)
        if verdict is None or not needs_grounding(question):
            questions.append(question)
            continue
        questions.append(
            question.model_copy(
                update={
                    "kind": "guidance",
                    "answer": trim_to_budget(verdict.answer) or question.answer,
                }
            )
        )
    return prepared.model_copy(update={"questions": questions})


def generate_prepared_interview(
    client: OpenAI,
    definition: UseCaseDefinition,
    answers: dict[str, str],
    experiences: list[CVExperience],
    cv_text: str = "",
) -> PreparedInterview:
    usable = experiences[: definition.experience_limit] if definition.experience_limit else []
    completion = client.chat.completions.create(
        model=INTERVIEW_QUESTIONS_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": build_prompt(definition, answers, experiences, cv_text),
            }
        ],
    )

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        raise ValueError("OpenAI response did not contain content")

    prepared = PreparedInterview.model_validate_json(content)
    if prepared.use_case_id != definition.catalog.id:
        raise ValueError("OpenAI response use_case_id does not match request")

    material = "\n".join(
        [answers.get(question.id, "") for question in definition.catalog.questions
         if question.id != "job_offer"]
        + [f"{item.title} - {item.company} - {item.period}" for item in usable]
        + [cv_text.strip() if definition.experience_limit else ""]
    ).strip()
    prepared = verify_grounding(client, material or "(rien)", prepared)

    # The page is bounded here rather than trusted to the prompt.
    return prepared.model_copy(
        update={
            "questions": [
                question.model_copy(
                    update={
                        "intent": trim_to_budget(question.intent, MAX_INTENT_CHARACTERS),
                        "answer": trim_to_budget(question.answer),
                        "kind": settle_kind(question.answer, question.kind),
                    }
                )
                for question in prepared.questions
            ]
        }
    )
