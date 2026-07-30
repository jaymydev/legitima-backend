from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


INTERVIEW_PREPARATION_MODEL = "gpt-4o-mini"
QUESTIONNAIRE_VERSION = "1.3"


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    helper: str
    required: bool = True
    input_type: str = "long_text"
    options: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


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


class PremiumKickoffRequest(BaseModel):
    """First premium computation, run right after the purchase.

    It works from the lean context alone — no guided question has been asked
    yet — so the user gets one usable answer before any further effort.
    """

    model_config = ConfigDict(extra="forbid")

    context: InterviewPreparationContext


class PremiumKickoffResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objection: str = Field(min_length=1)
    defensible_answer: str = Field(min_length=1)


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
    suggestions: list[str] | None = None,
) -> InterviewQuestion:
    return InterviewQuestion(
        id=question_id,
        title=title,
        helper=helper,
        required=required,
        input_type=input_type,
        options=options or [],
        suggestions=suggestions or _ANSWER_SUGGESTIONS.get(question_id, []),
    )


_ANSWER_SUGGESTIONS = {
    "company_context": ["Reprenez une mission clé de l’annonce.", "Citez un enjeu récent de l’entreprise qui vous intéresse."],
    "key_strengths": ["Associez chaque force à une exigence du poste.", "Choisissez deux qualités illustrées par votre parcours."],
    "proof_example": ["Décrivez la situation, votre action, puis le résultat.", "Choisissez un exemple où votre rôle personnel est clair."],
    "measurable_impact": ["Indiquez un délai, un volume ou une amélioration vérifiable.", "À défaut de chiffre, décrivez un effet concret observé."],
    "feared_question": ["Écrivez la question exactement comme le recruteur pourrait la poser.", "Pensez au point de votre parcours qui nécessite le plus d’explication."],
    "desired_takeaway": ["Formulez une seule idée forte liée au poste.", "Commencez par : « Je veux qu’il retienne que… »"],
    "questions_to_ask": ["Interrogez les priorités des premiers mois.", "Demandez comment la réussite sera évaluée sur ce poste."],
    "current_internal_role": ["Précisez votre mission, votre ancienneté et vos interlocuteurs.", "Résumez votre responsabilité principale en une phrase."],
    "target_internal_role": ["Nommez le poste ou l’équipe visée.", "Précisez le nouveau périmètre souhaité."],
    "mobility_motivation": ["Reliez votre motivation à une progression professionnelle.", "Expliquez pourquoi cette mobilité est cohérente maintenant."],
    "transferable_contributions": ["Citez une réalisation connue dans l’entreprise.", "Mentionnez une collaboration utile pour la future équipe."],
    "readiness_gaps": ["Identifiez une compétence à développer sans vous dévaloriser.", "Associez chaque écart à une action d’apprentissage."],
    "internal_objection": ["Écrivez-la telle que votre interlocuteur la formulerait.", "Pensez au point de votre parcours qui demande le plus d’explication."],
    "evolution_reservation": ["Écrivez la réserve telle que votre manager l’exprimerait.", "Pensez à ce qu’on vous a déjà opposé sur ce sujet."],
    "midyear_feared_topic": ["Écrivez le sujet tel qu’il sera amené.", "Pensez à l’écart le plus visible depuis le début de l’année."],
    "annual_feared_question": ["Écrivez la question exactement comme votre manager la poserait.", "Pensez à l’objectif non atteint ou à la période la plus discutable."],
    "performance_feared_critique": ["Écrivez la critique telle qu’elle sera formulée.", "Pensez au reproche que vous redoutez le plus d’entendre."],
    "internal_transition_plan": ["Proposez une passation et un calendrier réalistes.", "Précisez comment préserver la continuité de l’activité."],
    "current_scope": ["Distinguez responsabilités officielles et responsabilités déjà prises.", "Citez le périmètre, l’autonomie et les décisions assumées."],
    "desired_evolution": ["Nommez précisément le niveau ou les responsabilités souhaités.", "Expliquez ce qui changerait concrètement dans votre rôle."],
    "readiness_evidence": ["Citez une responsabilité déjà exercée au niveau supérieur.", "Appuyez-vous sur un résultat ou une reconnaissance vérifiable."],
    "business_impact": ["Reliez l’évolution à un besoin de l’équipe.", "Décrivez le bénéfice attendu pour l’organisation."],
    "development_areas": ["Présentez un axe de progrès et votre plan pour le travailler.", "Choisissez un point réel mais compatible avec l’évolution visée."],
    "evolution_conditions": ["Proposez des critères observables et une échéance.", "Demandez un point de suivi et les moyens nécessaires."],
    "role_context": ["Résumez votre mission et vos responsabilités principales.", "Précisez le périmètre dont vous êtes directement responsable."],
    "objectives_progress": ["Classez les objectifs : atteint, en cours ou retardé.", "Ajoutez un résultat ou une prochaine étape pour chacun."],
    "achievements": ["Choisissez deux contributions à impact concret.", "Décrivez votre action personnelle et l’effet obtenu."],
    "obstacles": ["Exposez le fait, son impact et la réponse apportée.", "Distinguez ce qui dépendait de vous du contexte externe."],
    "next_priorities": ["Citez trois priorités maximum pour le prochain semestre.", "Associez chaque priorité à un résultat attendu."],
    "support_needed": ["Demandez un arbitrage, une ressource ou une clarification précise.", "Expliquez ce que ce soutien permettra de sécuriser."],
    "role_scope": ["Décrivez les missions exercées et leur évolution dans l’année.", "Mentionnez les responsabilités nouvelles ou élargies."],
    "year_highlights": ["Sélectionnez les deux ou trois faits les plus significatifs.", "Privilégiez les contributions avec un effet observable."],
    "objectives_results": ["Pour chaque objectif, donnez le résultat et le contexte.", "Expliquez factuellement les écarts éventuels."],
    "skills_growth": ["Nommez la compétence puis son usage concret.", "Citez une situation où cette compétence a changé votre façon d’agir."],
    "difficulties": ["Présentez les causes, les conséquences et ce que vous avez appris.", "Restez factuel et proposez une piste d’amélioration."],
    "career_direction": ["Précisez l’expertise ou la responsabilité que vous souhaitez développer.", "Reliez votre souhait à un besoin de l’organisation."],
    "next_year_goals": ["Formulez des objectifs observables et réalistes.", "Ajoutez une échéance ou un indicateur quand c’est possible."],
    "expectations": ["Reprenez les objectifs et critères qui avaient été annoncés.", "Précisez les échéances ou niveaux attendus."],
    "measurable_results": ["Citez des chiffres, délais ou livrables vérifiables.", "Expliquez votre contribution personnelle au résultat."],
    "performance_gaps": ["Reformulez la critique précisément, sans la minimiser.", "Distinguez le fait observé de votre interprétation."],
    "context_factors": ["Séparez contraintes externes et décisions personnelles.", "Expliquez l’impact du contexte sans vous déresponsabiliser."],
    "improvement_actions": ["Décrivez une action déjà engagée et son premier effet.", "Précisez la méthode ou le suivi mis en place."],
    "support_and_commitments": ["Formulez ce que vous demandez et ce que vous vous engagez à faire.", "Ajoutez une échéance de suivi mesurable."],
}


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
                _question("internal_objection", "Quelle objection interne redoutez-vous ?", "Formulez-la telle qu’elle pourrait vous être opposée."),
                _question("readiness_gaps", "Quels écarts devez-vous encore combler ?", "Compétences, exposition métier ou expérience à acquérir.", required=False),
                _question("internal_transition_plan", "Comment faciliteriez-vous la transition ?", "Passation, calendrier, continuité de service et prise de poste.", required=False),
            ],
        ),
        analysis_focus="Construire un argumentaire de mobilité qui valorise la connaissance de l’organisation et démontre les compétences transférables. Nommer l’objection interne la plus probable et y répondre de façon défendable, en ancrant la légitimité du candidat dans ce que son parcours démontre déjà.",
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
                _question("evolution_reservation", "Quelle réserve pourrait-on vous opposer ?", "Formulez-la telle que votre interlocuteur l’exprimerait."),
                _question("development_areas", "Quels axes devez-vous encore renforcer ?", "Présentez-les avec lucidité et proposez une manière de progresser.", required=False),
                _question("evolution_conditions", "Quelles prochaines étapes souhaitez-vous convenir ?", "Critères, calendrier, accompagnement ou objectifs de validation."),
            ],
        ),
        analysis_focus="Préparer une demande d’évolution fondée sur des preuves de maturité, l’impact attendu et des prochaines étapes concrètes, sans transformer l’entretien en revendication abstraite. Anticiper la réserve que l’interlocuteur opposera et fournir une réponse défendable adossée aux faits fournis.",
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
                _question("midyear_feared_topic", "Quel sujet redoutez-vous de voir arriver ?", "Formulez-le tel qu’il sera amené dans l’échange."),
                _question("next_priorities", "Quelles sont vos priorités pour les six prochains mois ?", "Indiquez ce que vous voulez sécuriser ou faire progresser."),
                _question("support_needed", "De quel soutien avez-vous besoin ?", "Arbitrage, moyens, formation, disponibilité ou clarification.", required=False),
            ],
        ),
        analysis_focus="Produire un bilan intermédiaire factuel, préparer les arbitrages et formuler des demandes de soutien concrètes. Anticiper le sujet qui sera opposé au candidat et préparer une réponse défendable qui assume les faits sans les subir.",
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
                _question("annual_feared_question", "Quelle question difficile redoutez-vous ?", "Formulez-la telle que votre manager pourrait la poser."),
                _question("career_direction", "Quelle évolution souhaitez-vous ?", "Responsabilités, expertise, mobilité ou conditions de réussite."),
                _question("next_year_goals", "Quels objectifs proposez-vous pour l’année à venir ?", "Formulez des priorités réalistes et observables."),
            ],
        ),
        analysis_focus="Créer un bilan annuel équilibré, étayer la contribution et préparer une discussion d’évolution réaliste. Anticiper la question difficile que le manager posera et construire une réponse défendable : assumer l’écart, le requalifier par la trajectoire, et rattacher la suite à ce que le parcours démontre.",
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
                _question("performance_feared_critique", "Quelle critique redoutez-vous le plus ?", "Formulez-la telle qu’elle pourrait vous être adressée."),
                _question("improvement_actions", "Qu’avez-vous déjà engagé pour progresser ?", "Actions, nouvelles méthodes, suivi ou apprentissage."),
                _question("support_and_commitments", "Quels soutiens et engagements proposer ?", "Précisez ce que vous demandez et ce que vous vous engagez à faire."),
            ],
        ),
        analysis_focus="Préparer une réponse responsable et factuelle, distinguer résultats et contexte, puis proposer un plan d’amélioration mesurable. Anticiper la critique la plus dure qui sera formulée et y répondre de façon défendable, sans se dévaloriser ni nier les faits.",
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


def has_usable_context(context: InterviewPreparationContext) -> bool:
    """Whether there is enough material to build an answer from.

    Without a role or a career path there is nothing to reason from, and the
    only way to produce an answer would be to invent one.
    """
    return bool(
        context.target_role.strip()
        or context.career_experiences.strip()
        or context.freemium_analysis.strip()
    )


def generate_kickoff(
    client: OpenAI,
    context: InterviewPreparationContext,
) -> PremiumKickoffResponse:
    """Name the objection this profile will actually meet, and answer it.

    Deliberately narrow: one objection, one answer. This runs while the user
    waits on a blocking screen just after paying, so it must be fast and must
    land on the single thing the free teaser raised without resolving.
    """
    prompt = f"""
Tu prépares un candidat à un entretien à partir de son analyse gratuite, juste
après son achat. Il n'a encore répondu à aucune question guidée.

Objectif : nommer l'objection la plus probable que son interlocuteur soulèvera,
puis lui donner une réponse défendable qu'il peut prononcer telle quelle.

INTERDICTION CENTRALE — n'affirme jamais ce que la personne a FAIT pendant la
période sensible. Si le contexte ne l'écrit pas noir sur blanc, tu ne le sais
pas, et le candidat serait pris en défaut à la question de suivi. Sont
notamment interdits, sauf s'ils figurent littéralement dans le contexte :
« je me suis formé », « j'ai suivi les tendances du marché », « j'ai pris du
recul », « j'ai réfléchi à mes objectifs », « j'ai exploré de nouvelles
opportunités », « j'ai approfondi mes connaissances », et toute autre activité
que tu devrais supposer.

La requalification porte sur la TRAJECTOIRE, jamais sur le contenu de la
période : ce que le parcours démontre avant, ce vers quoi il va après, et en
quoi cette étape sert le poste visé. Une transition se défend par sa cohérence
d'ensemble, pas par le récit de ce qui l'a remplie.

Règles impératives :
- réponds uniquement en français ;
- utilise exclusivement les informations fournies ;
- n'invente aucune expérience, entreprise, date, compétence, diplôme ou résultat ;
- ne minimise pas et ne masque pas la zone sensible : nomme-la sans détour ;
- reste professionnel, factuel et non-jugeant ;
- ne promets aucun succès à l'embauche ;
- si l'analyse gratuite cite déjà une objection probable, reprends celle-là ;
- l'objection est une question courte, telle qu'un recruteur la poserait ;
- la réponse fait 2 à 4 phrases, à la première personne, appuyée uniquement sur
  les étapes réellement mentionnées, et se termine sur ce que le parcours
  apporte au poste visé ;
- mieux vaut une réponse courte et entièrement vérifiable qu'une réponse
  étoffée dont une phrase serait invérifiable.

Retourne uniquement un objet JSON respectant exactement cette structure :
{{
  "objection": "",
  "defensible_answer": ""
}}

Contexte disponible :
{json.dumps(context.model_dump(), ensure_ascii=False)}
"""
    completion = client.chat.completions.create(
        model=INTERVIEW_PREPARATION_MODEL,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        raise ValueError("OpenAI response did not contain content")

    return PremiumKickoffResponse.model_validate_json(content)
