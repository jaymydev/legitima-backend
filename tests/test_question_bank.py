"""La banque écrite à la main, et sa sélection.

La propriété qui compte : servir une page utile sans aucun appel modèle, donc
sans clé, sans attente et sans invention. C'est ce que la génération ne savait
pas faire pour quelqu'un qui n'a rien saisi.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.api import errors
from app.main import app
from app.services import bank_selection as selection
from app.services import question_bank as bank

client = TestClient(app)

ALL_GROUPS = [
    bank.COMMUNES, bank.SITUATIONS, bank.DEPLACEES, bank.ETAPES, bank.RECRUTEMENT,
    bank.MOBILITE, bank.EVOLUTION, bank.ANNUEL, bank.MI_ANNEE, bank.PERFORMANCE,
    bank.METIER_DEV_BACK, bank.METIER_COMMERCE, bank.METIER_COMPTA,
]
ALL_ENTRIES = [entry for group in ALL_GROUPS for entry in group]

#: Le vocabulaire arrêté. Une balise hors liste ne pourra jamais se remplir.
KNOWN_SLOTS = {
    "<PRÉNOM>", "<MÉTIER>", "<NOMBRE_ANNÉES_EXPÉRIENCE>", "<POSTE_ACTUEL>",
    "<ENTREPRISE_ACTUELLE>", "<ANCIENNETÉ>", "<POSTE_PRÉCÉDENT>", "<ENTREPRISE_PRÉCÉDENTE>",
    "<POSTE_VISÉ>", "<ENTREPRISE_VISÉE>", "<SITE_VISÉ>", "<ÉQUIPE_VISÉE>",
    "<MISSION_DE_L_OFFRE>", "<RÉALISATION>", "<CE_QUE_J_AI_FAIT>", "<RÉSULTAT>",
    "<CHIFFRE>", "<DIFFICULTÉ>", "<COMPÉTENCE>", "<OUTIL>", "<CE_QUI_VOUS_ATTIRE>",
    "<OBJECTIF>", "<AVANCEMENT>", "<POINT_À_AMÉLIORER>", "<PRÉTENTION_BASSE>",
    "<PRÉTENTION_HAUTE>", "<SALAIRE_ACTUEL>", "<PLANCHER>", "<AVANTAGE>",
    "<AUGMENTATION_DEMANDÉE>", "<PRÉAVIS>", "<RÉALISATION_2>", "<RÉSULTAT_2>",
    "<COMPÉTENCE_2>", "<OBJECTIF_2>", "<AVANCEMENT_2>", "<AVANTAGE_2>", "<CHIFFRE_2>",
}


def test_the_bank_holds_what_was_written() -> None:
    assert len(ALL_ENTRIES) == 194
    assert len({entry.id for entry in ALL_ENTRIES}) == len(ALL_ENTRIES)


def test_no_entry_uses_a_slot_outside_the_vocabulary() -> None:
    """Une balise inventée ne se remplira jamais : rien ne saura quoi y mettre.

    C'est la seule règle qui doit tenir sur 194 entrées écrites à la main, donc
    elle est vérifiée plutôt que recommandée.
    """
    used = set()
    for entry in ALL_ENTRIES:
        used.update(re.findall(r"<[A-ZÉÈÀÎÔÛ_0-9]+>", entry.answer + entry.follow_up))
    assert used - KNOWN_SLOTS == set()


def test_no_review_commentary_leaked_into_the_bank() -> None:
    """La colonne 3 du tableur jugeait la banque ; elle n'a rien à faire dedans."""
    for entry in ALL_ENTRIES:
        assert "Question de connaissance" not in entry.answer
        assert "Entrée à" not in entry.answer


@pytest.mark.parametrize("use_case_id", sorted(selection.PLANS))
def test_every_type_serves_a_full_page_with_no_input_at_all(use_case_id: str) -> None:
    """La promesse du pivot, vérifiée sans clé et sans réseau."""
    page = selection.select(use_case_id)

    assert page is not None
    assert len(page.entries) == selection.PAGE_SIZE
    assert all(entry.question for entry in page.entries)


@pytest.mark.parametrize("use_case_id", sorted(selection.PLANS))
def test_every_type_has_a_plan_before_entering(use_case_id: str) -> None:
    """« J'ai 5 minutes pour réviser » : chaque type sert son bloc, tel quel.

    Trois gestes maximum — au-delà ce n'est plus un plan, c'est une révision.
    Aucune balise : ce bloc ne se remplit pas, il se lit dans le couloir.
    Et jamais le mot « objection » : le recruteur n'est pas un adversaire.
    """
    plan = bank.ACTION_PLANS[use_case_id]

    assert 1 <= len(plan) <= 3
    for gesture in plan:
        assert gesture.strip()
        assert "<" not in gesture
        assert "objection" not in gesture.lower()


def test_the_route_serves_the_plan_with_the_page() -> None:
    response = client.get("/v3/interview/bank?use_case_id=recruitment")

    assert response.status_code == 200
    assert response.json()["action_plan"] == bank.ACTION_PLANS["recruitment"]


def test_a_second_preparation_brings_new_questions() -> None:
    first = selection.select("recruitment")
    second = selection.select("recruitment", seen={e.id for e in first.entries})

    assert not ({e.id for e in second.entries} & {e.id for e in first.entries})


def test_an_exhausted_bank_still_serves_a_full_page() -> None:
    """Une page complète vaut mieux qu'une page neuve.

    Quand tout a été vu, on repasse sur les questions les plus probables plutôt
    que de rendre trois lignes : ce sont elles qui tomberont de toute façon.
    """
    everything = {entry.id for entry in ALL_ENTRIES}
    page = selection.select("recruitment", seen=everything)

    assert len(page.entries) == selection.PAGE_SIZE


def test_a_metier_takes_the_front_of_the_page() -> None:
    page = selection.select("recruitment", metier="developpement_back")
    technical = {entry.id for entry in bank.METIER_DEV_BACK}

    assert sum(1 for entry in page.entries[:3] if entry.id in technical) == 3
    assert len(page.entries) == selection.PAGE_SIZE


def test_an_annual_review_is_never_asked_about_children() -> None:
    """Les questions déplacées ne sont servies que là où elles arrivent.

    Un entretien annuel avec son propre manager n'est pas le lieu du « vous
    comptez avoir des enfants » — l'y glisser inquiéterait pour rien.
    """
    displaced = {entry.id for entry in bank.DEPLACEES}
    for use_case_id in ("annual_review", "mid_year", "performance_review", "role_evolution"):
        page = selection.select(use_case_id)
        assert not ({entry.id for entry in page.entries} & displaced), use_case_id


def test_the_route_needs_no_model_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.get(
        "/v3/interview/bank",
        params={"use_case_id": "performance_review"},
        headers={"X-Forwarded-For": "198.51.100.80"},
    )

    assert response.status_code == 200
    assert len(response.json()["questions"]) == selection.PAGE_SIZE


def test_the_route_keeps_the_slots_intact() -> None:
    """Les gabarits partent avec leurs balises : ils sont remplis sur l'appareil,
    pour qu'un salaire n'ait jamais besoin d'atteindre le serveur."""
    response = client.get(
        "/v3/interview/bank",
        params={"use_case_id": "recruitment"},
        headers={"X-Forwarded-For": "198.51.100.81"},
    )

    body = " ".join(q["answer"] for q in response.json()["questions"])
    assert "<" in body and ">" in body


def test_an_unknown_type_is_refused() -> None:
    response = client.get(
        "/v3/interview/bank",
        params={"use_case_id": "coffee_chat"},
        headers={"X-Forwarded-For": "198.51.100.82"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == errors.UNKNOWN_USE_CASE
