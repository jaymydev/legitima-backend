from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


INTERVIEW_PREPARATION_MODEL = "gpt-4o-mini"
QUESTIONNAIRE_VERSION = "1.1"


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    helper: str
    required: bool = True
    input_type: str = "long_text"
    options: list[str] = Field(default_factory=list)


class InterviewUseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    short_title: str
    description: str
    questionnaire_version: str
    questions: list[InterviewQuestion]


class InterviewAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    answer: str = Field(min_length=1, max_length=5000)


class InterviewPreparationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(default="", max_length=5000)
    career_experiences: str = Field(default="", max_length=10000)
    sensitive_point: str = Field(default="", max_length=5000)
    freemium_analysis: str = Field(default="", max_length=15000)


class InterviewPreparationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    questionnaire_version: str
    answers: list[InterviewAnswer] = Field(min_length=1)
    context: Optional[InterviewPreparationContext] = None


class PreparationSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class InterviewPreparationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sections: list[PreparationSection] = Field(min_length=1)
    talking_points: list[str] = Field(min_length=1)
    action_plan: list[str] = Field(min_length=1)


@dataclass(frozen=True)
class UseCaseDefinition:
    catalog: InterviewUseCase
    analysis_focus: str


def _question(
    question_id: str,
    title: str,
    helper: str,
    *,
    required: bool = True,
    input_type: str = "long_text",
    options: list[str] | None = None,
) -> InterviewQuestion:
    return InterviewQuestion(
        id=question_id,
        title=title,
        helper=helper,
        required=required,
        input_type=input_type,
        options=options or [],
    )


USE_CASES: dict[str, UseCaseDefinition] = {
    "recruitment": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="recruitment",
            title="Entretien de recrutement",
            short_title="Recrutement",
            description="Préparer un récit clair, des preuves de légitimité et des réponses aux objections.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question(
                    "interview_stage",
                    "Où en êtes-vous dans le processus ?",
                    "Choisissez l’étape de votre prochain échange.",
                    input_type="single_choice",
                    options=["Premier échange", "Entretien RH", "Entretien manager", "Entretien technique", "Entretien final"],
                ),
                _question("company_context", "Que savez-vous du poste ou de l’entreprise ?", "Quelques éléments de l’annonce ou du contexte suffisent.", required=False),
                _question(
                    "interviewer",
                    "Avec qui allez-vous échanger ?",
                    "Sélectionnez l’interlocuteur principal si vous le connaissez.",
                    required=False,
                    input_type="single_choice",
                    options=["Recruteur", "Manager", "Direction", "Équipe technique", "Inconnu"],
                ),
                _question("key_strengths", "Quelles sont les deux forces à faire retenir ?", "Choisissez les forces les plus utiles pour ce poste."),
                _question("proof_example", "Quel exemple concret prouve le mieux l’une de ces forces ?", "Appuyez-vous sur une expérience déjà renseignée."),
                _question("measurable_impact", "Quel résultat ou impact pouvez-vous mentionner ?", "Laissez vide si vous ne disposez pas d’un fait vérifiable.", required=False),
                _question("feared_question", "Quelle question craignez-vous le plus ?", "Formulez la question telle qu’elle pourrait être posée."),
                _question(
                    "secondary_topic",
                    "Y a-t-il un autre sujet à préparer ?",
                    "Choisissez le sujet secondaire le plus utile.",
                    required=False,
                    input_type="single_choice",
                    options=["Salaire", "Manque d’expérience", "Reconversion", "Interruption", "Départ d’un poste", "Mobilité"],
                ),
                _question(
                    "answer_tone",
                    "Quel ton voulez-vous adopter ?",
                    "Ce choix guidera la formulation des réponses sensibles.",
                    input_type="single_choice",
                    options=["Direct et factuel", "Rassurant", "Diplomatique"],
                ),
                _question("desired_takeaway", "À la fin, que doit avoir compris votre interlocuteur ?", "Résumez en une phrase l’impression que vous voulez laisser."),
                _question("questions_to_ask", "Qu’aimeriez-vous demander au recruteur ?", "Ajoutez une ou deux questions si vous en avez.", required=False),
                _question(
                    "preparation_depth",
                    "Quel niveau de préparation souhaitez-vous ?",
                    "Choisissez le niveau de détail du résultat final.",
                    input_type="single_choice",
                    options=["Fiche express", "Préparation complète"],
                ),
            ],
        ),
        analysis_focus="Produire un kit d’entretien directement utilisable : pitch oral, réponse de présentation, preuves de légitimité, réponses difficiles, objections probables, questions à poser et checklist finale.",
    ),
    "internal_mobility": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="internal_mobility",
            title="Entretien de mobilité interne",
            short_title="Mobilité interne",
            description="Présenter une transition cohérente vers une autre équipe ou un autre métier dans l’organisation.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question("current_internal_role", "Quel est votre rôle actuel dans l’organisation ?", "Résumez votre périmètre, votre ancienneté et vos interlocuteurs principaux."),
                _question("target_internal_role", "Quelle mobilité interne visez-vous ?", "Précisez le poste, l’équipe ou le métier souhaité."),
                _question("mobility_motivation", "Pourquoi souhaitez-vous cette mobilité ?", "Expliquez ce que vous cherchez à développer et la cohérence avec votre parcours interne."),
                _question("transferable_contributions", "Quelles contributions internes soutiennent votre candidature ?", "Citez des réalisations, connaissances de l’organisation ou collaborations transférables."),
                _question("readiness_gaps", "Quels écarts devez-vous encore combler ?", "Compétences, exposition métier ou expérience à acquérir.", required=False),
                _question("internal_transition_plan", "Comment faciliteriez-vous la transition ?", "Passation, calendrier, continuité de service et prise de poste.", required=False),
            ],
        ),
        analysis_focus="Construire un argumentaire de mobilité qui valorise la connaissance de l’organisation, démontre les compétences transférables et prépare une transition responsable.",
    ),
    "role_evolution": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="role_evolution",
            title="Entretien d’évolution de poste",
            short_title="Évolution de poste",
            description="Démontrer que vos résultats et votre progression justifient un périmètre élargi ou une promotion.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question("current_scope", "Quel est votre périmètre actuel ?", "Décrivez vos responsabilités officielles et celles déjà exercées au-delà du poste."),
                _question("desired_evolution", "Quelle évolution demandez-vous ?", "Précisez le niveau, les responsabilités ou le périmètre souhaité."),
                _question("readiness_evidence", "Quels faits montrent que vous êtes prêt ?", "Responsabilités prises, décisions, résultats ou reconnaissance reçue."),
                _question("business_impact", "Quel impact cette évolution permettrait-elle ?", "Reliez votre demande aux besoins de l’équipe ou de l’organisation."),
                _question("development_areas", "Quels axes devez-vous encore renforcer ?", "Présentez-les avec lucidité et proposez une manière de progresser.", required=False),
                _question("evolution_conditions", "Quelles prochaines étapes souhaitez-vous convenir ?", "Critères, calendrier, accompagnement ou objectifs de validation."),
            ],
        ),
        analysis_focus="Préparer une demande d’évolution fondée sur des preuves de maturité, l’impact attendu et des prochaines étapes concrètes, sans transformer l’entretien en revendication abstraite.",
    ),
    "mid_year": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="mid_year",
            title="Entretien de mi-année",
            short_title="Mi-année",
            description="Faire le point sur l’avancement, les obstacles et les priorités du prochain semestre.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question("role_context", "Quel est votre rôle actuel ?", "Résumez vos responsabilités et votre périmètre."),
                _question("objectives_progress", "Où en êtes-vous sur vos objectifs ?", "Distinguez ce qui est terminé, en cours ou retardé."),
                _question("achievements", "Quelles contributions voulez-vous mettre en avant ?", "Mentionnez des résultats ou effets concrets."),
                _question("obstacles", "Quels obstacles avez-vous rencontrés ?", "Décrivez les faits et leur impact, sans chercher de responsable.", required=False),
                _question("next_priorities", "Quelles sont vos priorités pour les six prochains mois ?", "Indiquez ce que vous voulez sécuriser ou faire progresser."),
                _question("support_needed", "De quel soutien avez-vous besoin ?", "Arbitrage, moyens, formation, disponibilité ou clarification.", required=False),
            ],
        ),
        analysis_focus="Produire un bilan intermédiaire factuel, préparer les arbitrages et formuler des demandes de soutien concrètes.",
    ),
    "annual_review": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="annual_review",
            title="Entretien annuel",
            short_title="Annuel",
            description="Structurer le bilan de l’année, l’évolution souhaitée et les objectifs à venir.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question("role_scope", "Quel a été votre périmètre cette année ?", "Décrivez vos missions et les évolutions de responsabilité."),
                _question("year_highlights", "Quels sont les faits marquants de votre année ?", "Sélectionnez les contributions les plus significatives."),
                _question("objectives_results", "Quels objectifs ont été atteints ou non atteints ?", "Ajoutez les résultats disponibles et le contexte utile."),
                _question("skills_growth", "Quelles compétences avez-vous développées ?", "Précisez comment elles ont été mises en pratique."),
                _question("difficulties", "Quelles difficultés doivent être abordées ?", "Restez factuel sur les causes et les conséquences.", required=False),
                _question("career_direction", "Quelle évolution souhaitez-vous ?", "Responsabilités, expertise, mobilité ou conditions de réussite."),
                _question("next_year_goals", "Quels objectifs proposez-vous pour l’année à venir ?", "Formulez des priorités réalistes et observables."),
            ],
        ),
        analysis_focus="Créer un bilan annuel équilibré, étayer la contribution et préparer une discussion d’évolution réaliste.",
    ),
    "performance_review": UseCaseDefinition(
        catalog=InterviewUseCase(
            id="performance_review",
            title="Entretien de performance",
            short_title="Performance",
            description="Préparer une discussion factuelle sur les résultats, les écarts et le plan d’amélioration.",
            questionnaire_version=QUESTIONNAIRE_VERSION,
            questions=[
                _question("expectations", "Quelles attentes ou objectifs avaient été fixés ?", "Reprenez les critères connus et les échéances."),
                _question("measurable_results", "Quels résultats pouvez-vous démontrer ?", "Ajoutez des indicateurs ou exemples vérifiables."),
                _question("performance_gaps", "Quels écarts ou critiques ont été formulés ?", "Décrivez-les précisément, sans les minimiser.", required=False),
                _question("context_factors", "Quels facteurs de contexte ont influencé les résultats ?", "Séparez les faits externes de vos propres décisions.", required=False),
                _question("improvement_actions", "Qu’avez-vous déjà engagé pour progresser ?", "Actions, nouvelles méthodes, suivi ou apprentissage."),
                _question("support_and_commitments", "Quels soutiens et engagements proposer ?", "Précisez ce que vous demandez et ce que vous vous engagez à faire."),
            ],
        ),
        analysis_focus="Préparer une réponse responsable et factuelle, distinguer résultats et contexte, puis proposer un plan d’amélioration mesurable.",
    ),
}


def list_use_cases() -> list[InterviewUseCase]:
    return [definition.catalog for definition in USE_CASES.values()]


def get_use_case(use_case_id: str) -> UseCaseDefinition | None:
    return USE_CASES.get(use_case_id)


def validate_request(
    payload: InterviewPreparationRequest,
    definition: UseCaseDefinition,
) -> dict[str, str]:
    if payload.questionnaire_version != definition.catalog.questionnaire_version:
        raise ValueError("Questionnaire version is no longer supported")

    questions = {question.id: question for question in definition.catalog.questions}
    answers: dict[str, str] = {}
    for item in payload.answers:
        if item.question_id not in questions:
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


def generate_preparation(
    client: OpenAI,
    definition: UseCaseDefinition,
    answers: dict[str, str],
    context: Optional[InterviewPreparationContext] = None,
) -> InterviewPreparationResponse:
    question_titles = {question.id: question.title for question in definition.catalog.questions}
    input_items = [
        {"question": question_titles[question_id], "answer": answer}
        for question_id, answer in answers.items()
        if answer
    ]
    prompt = f"""
Tu prépares un utilisateur pour le cas suivant : {definition.catalog.title}.

Objectif spécifique :
{definition.analysis_focus}

Règles impératives :
- réponds uniquement en français ;
- utilise exclusivement les informations fournies ;
- n’invente aucun résultat, objectif, compétence ou événement ;
- reste professionnel, factuel et non-jugeant ;
- produis des formulations que l’utilisateur peut réellement employer pendant l’entretien ;
- évite les répétitions entre les sections.

Retourne uniquement un objet JSON respectant exactement cette structure :
{{
  "use_case_id": "{definition.catalog.id}",
  "title": "",
  "summary": "",
  "sections": [{{"title": "", "content": ""}}],
  "talking_points": [""],
  "action_plan": [""]
}}

Réponses de l’utilisateur :
{json.dumps(input_items, ensure_ascii=False)}

Contexte déjà collecté avant le premium, à réutiliser sans le redemander :
{json.dumps(context.model_dump() if context else {}, ensure_ascii=False)}
"""
    completion = client.chat.completions.create(
        model=INTERVIEW_PREPARATION_MODEL,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        raise ValueError("OpenAI response did not contain content")

    response = InterviewPreparationResponse.model_validate_json(content)
    if response.use_case_id != definition.catalog.id:
        raise ValueError("OpenAI response use_case_id does not match request")
    return response
