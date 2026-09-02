"""Choisir les questions à servir. Aucun appel modèle, donc instantané et gratuit.

La banque est ordonnée par probabilité décroissante, et cet ordre est la donnée.
Sélectionner revient donc à prendre les premières de chaque source, en excluant
ce que la personne a déjà vu.

Sur la fraîcheur : la consigne était « de nouvelles questions à chaque demande ».
Une banque finie ne peut pas le tenir indéfiniment, et surtout elle ne le devrait
pas — préparer deux fois le même entretien et se voir proposer des questions
moins probables la seconde fois serait un mauvais service. On exclut donc ce qui
a été vu récemment, et quand une source est épuisée on y revient plutôt que de
rendre une page plus courte.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.question_bank import (
    ANNUEL,
    BankEntry,
    COMMUNES,
    DEPLACEES,
    EVOLUTION,
    METIER_COMMERCE,
    METIER_COMPTA,
    METIER_CYBER,
    METIER_DATA,
    METIER_DEV_BACK,
    METIER_DEV_FRONT,
    METIER_LOGISTIQUE,
    METIER_MARKETING,
    METIER_OPS,
    METIER_RH,
    MI_ANNEE,
    MOBILITE,
    PERFORMANCE,
    RECRUTEMENT,
    SITUATIONS,
)

PAGE_SIZE = 8

#: Combien d'entrées prendre à chaque source, par type d'entretien.
#:
#: Le type d'abord, parce que c'est ce que la personne est venue préparer. Puis
#: les communes et les mises en situation, qui tombent partout. Les questions
#: déplacées ne sont servies que là où elles arrivent vraiment : un entretien
#: annuel avec son propre manager n'est pas le lieu du « vous comptez avoir des
#: enfants ».
PLANS: dict[str, list[tuple[str, int]]] = {
    "recruitment": [("type", 4), ("communes", 2), ("situations", 1), ("deplacees", 1)],
    "internal_mobility": [("type", 4), ("communes", 2), ("situations", 2)],
    "role_evolution": [("type", 4), ("communes", 2), ("situations", 2)],
    "annual_review": [("type", 5), ("communes", 2), ("situations", 1)],
    "mid_year": [("type", 5), ("communes", 2), ("situations", 1)],
    "performance_review": [("type", 5), ("communes", 2), ("situations", 1)],
}

TYPE_SOURCES: dict[str, list[BankEntry]] = {
    "recruitment": RECRUTEMENT,
    "internal_mobility": MOBILITE,
    "role_evolution": EVOLUTION,
    "annual_review": ANNUEL,
    "mid_year": MI_ANNEE,
    "performance_review": PERFORMANCE,
}

#: Les entretiens où une verticale a un sens : ceux qui évaluent une compétence
#: pour un poste. Les questions métier sont écrites pour ça — « vendez-moi ce
#: stylo », « qu'est-ce que le cut-off » — et elles ne se posent pas quand on
#: fait le bilan d'un travail déjà fait, avec quelqu'un qui l'a suivi toute
#: l'année. Les servir là occupait les trois premières places d'une page de huit
#: avec des questions de probabilité nulle, en évinçant « parlez-moi de vous ».
TYPES_EVALUATION: frozenset[str] = frozenset(
    {"recruitment", "internal_mobility", "role_evolution"}
)

#: Les verticales métier ne remplacent pas le transversal, elles s'y ajoutent :
#: un entretien technique est aussi un entretien.
METIERS: dict[str, list[BankEntry]] = {
    "developpement_back": METIER_DEV_BACK,
    "developpement_front": METIER_DEV_FRONT,
    "data": METIER_DATA,
    "ops": METIER_OPS,
    "cybersecurite": METIER_CYBER,
    "commerce": METIER_COMMERCE,
    "comptabilite": METIER_COMPTA,
    "ressources_humaines": METIER_RH,
    "marketing": METIER_MARKETING,
    "logistique": METIER_LOGISTIQUE,
}

#: Ce que l'app affiche pour chaque verticale. Servi par le catalogue plutôt
#: que codé côté client : une verticale ajoutée ici apparaît dans l'app sans
#: nouvelle version.
METIER_LABELS: dict[str, str] = {
    "developpement_back": "Développement back-end",
    "developpement_front": "Développement front-end",
    "data": "Data",
    "ops": "Ops / infrastructure",
    "cybersecurite": "Cybersécurité",
    "commerce": "Commerce / vente",
    "comptabilite": "Comptabilité",
    "ressources_humaines": "Ressources humaines",
    "marketing": "Marketing",
    "logistique": "Logistique",
}

SHARED_SOURCES: dict[str, list[BankEntry]] = {
    "communes": COMMUNES,
    "situations": SITUATIONS,
    "deplacees": DEPLACEES,
}


@dataclass(frozen=True)
class Selection:
    use_case_id: str
    entries: list[BankEntry]


def _take(source: list[BankEntry], count: int, seen: set[str], picked: set[str]) -> list[BankEntry]:
    fresh = [e for e in source if e.id not in seen and e.id not in picked]
    chosen = fresh[:count]
    if len(chosen) < count:
        # Source épuisée par les exclusions : on y revient plutôt que de rendre
        # une page plus courte. Une page complète vaut mieux qu'une page neuve.
        already = [e for e in source if e.id not in picked and e not in chosen]
        chosen += already[: count - len(chosen)]
    picked.update(e.id for e in chosen)
    return chosen


def select(
    use_case_id: str,
    *,
    seen: set[str] | None = None,
    metier: str | None = None,
    encadrement: bool = False,
) -> Selection | None:
    plan = PLANS.get(use_case_id)
    if plan is None:
        return None

    seen = seen or set()
    picked: set[str] = set()
    entries: list[BankEntry] = []

    def usable(source: list[BankEntry]) -> list[BankEntry]:
        # « Un membre de votre équipe décroche » servi à quelqu'un qui n'a pas
        # d'équipe le prépare à un entretien qui n'existe pas. Tant que rien ne
        # dit que la personne encadre, ces entrées restent au tiroir.
        if not encadrement:
            return [e for e in source if not e.encadrement]

        # Les sortir du tiroir ne suffisait pas : leur rang d'origine est écrit
        # pour quelqu'un qui n'a pas d'équipe, et il les plaçait hors de portée
        # d'une page — la première est septième des situations, dont on ne prend
        # qu'une ou deux. L'interrupteur promettait donc des questions que
        # personne ne voyait. Pour qui encadre, elles ne sont pas un supplément :
        # ce sont les plus probables de leur catégorie. L'ordre reste la donnée,
        # il est seulement relatif à qui demande.
        return [e for e in source if e.encadrement] + [e for e in source if not e.encadrement]

    metier_source = METIERS.get(metier or "") if use_case_id in TYPES_EVALUATION else None
    if metier_source:
        # Le métier passe devant : c'est là que se joue un entretien technique,
        # et c'est la moitié de la page qui n'a besoin d'aucune saisie.
        entries += _take(usable(metier_source), 3, seen, picked)

    for source_name, count in plan:
        source = (
            TYPE_SOURCES[use_case_id] if source_name == "type" else SHARED_SOURCES[source_name]
        )
        remaining = PAGE_SIZE - len(entries)
        if remaining <= 0:
            break
        entries += _take(usable(source), min(count, remaining), seen, picked)

    entries = entries[:PAGE_SIZE]

    if encadrement and not any(e.encadrement for e in entries):
        # La promesse de l'interrupteur ne souffre pas d'exception, or un métier
        # consomme trois places en tête et la page se remplit avant d'atteindre
        # les situations : un chef d'équipe qui renseignait sa spécialité
        # n'obtenait toujours rien. On lui garde la dernière place — la tête
        # reste au métier, qui l'a promise lui aussi.
        team = _take([e for e in SITUATIONS if e.encadrement], 1, seen, picked)
        if team:
            entries[-1] = team[0]

    return Selection(use_case_id=use_case_id, entries=entries)
