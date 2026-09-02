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
    bank.METIER_DEV_BACK, bank.METIER_DEV_FRONT, bank.METIER_DATA, bank.METIER_OPS,
    bank.METIER_CYBER, bank.METIER_COMMERCE, bank.METIER_COMPTA, bank.METIER_RH,
    bank.METIER_MARKETING, bank.METIER_LOGISTIQUE,
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
    assert len(ALL_ENTRIES) == 300
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


@pytest.mark.parametrize("metier", sorted(selection.METIERS))
def test_every_metier_takes_the_front_of_the_page(metier: str) -> None:
    page = selection.select("recruitment", metier=metier)
    technical = {entry.id for entry in selection.METIERS[metier]}

    assert sum(1 for entry in page.entries[:3] if entry.id in technical) == 3
    assert len(page.entries) == selection.PAGE_SIZE


@pytest.mark.parametrize("metier", sorted(selection.METIERS))
def test_every_metier_has_a_label_and_enough_entries(metier: str) -> None:
    """Une verticale servie sans libellé serait un slug à l'écran."""
    assert selection.METIER_LABELS[metier]
    assert len(selection.METIERS[metier]) >= 15


def test_the_metier_catalog_serves_labels() -> None:
    response = client.get("/v3/interview/metiers")

    assert response.status_code == 200
    payload = response.json()
    assert sorted(payload["metiers"]) == sorted(selection.METIERS)
    assert {"id": "cybersecurite", "label": "Cybersécurité"} in payload["catalog"]


def test_management_only_entries_stay_in_the_drawer() -> None:
    """« Un membre de votre équipe décroche » ne va qu'à qui a une équipe.

    Servie à quelqu'un qui n'encadre pas, l'entrée prépare à un entretien qui
    n'existe pas — et elle occupait une place qu'une question probable méritait.
    """
    management_ids = {entry.id for entry in ALL_ENTRIES if entry.encadrement}
    assert management_ids, "le tableur signalait des entrées encadrement : elles doivent être marquées"

    for use_case_id in sorted(selection.PLANS):
        page = selection.select(use_case_id)
        assert not ({e.id for e in page.entries} & management_ids)

    # Qui encadre les retrouve — même une fois toute la banque vue, le
    # rattrapage de page complète ne doit pas les faire fuiter chez les autres.
    exhausted = selection.select("recruitment", seen={entry.id for entry in ALL_ENTRIES})
    assert not ({e.id for e in exhausted.entries} & management_ids)
    with_team = selection.select("recruitment", seen=set(), encadrement=True)
    assert len(with_team.entries) == selection.PAGE_SIZE


def test_declaring_a_team_actually_brings_a_team_question() -> None:
    """L'interrupteur doit ajouter quelque chose, pas seulement ouvrir le tiroir.

    Ce test manquait, et c'est ce qui a laissé passer le défaut : on vérifiait
    que la page faisait bien huit entrées, jamais qu'une question d'encadrement
    y figurait. Elle n'y figurait pas — la première est septième des situations,
    dont un plan ne prend qu'une ou deux.
    """
    management_ids = {entry.id for entry in ALL_ENTRIES if entry.encadrement}

    for use_case_id in sorted(selection.PLANS):
        page = selection.select(use_case_id, encadrement=True)
        assert {e.id for e in page.entries} & management_ids, (
            f"{use_case_id} : « j'encadre une équipe » n'ajoute aucune question"
        )
        assert len(page.entries) == selection.PAGE_SIZE

    # Le métier consomme trois places en tête : la promesse doit tenir quand
    # même, et sans lui prendre les siennes.
    for use_case_id in sorted(selection.PLANS):
        for metier in selection.METIERS:
            page = selection.select(use_case_id, metier=metier, encadrement=True)
            ids = [e.id for e in page.entries]
            assert set(ids) & management_ids, (
                f"{use_case_id} + {metier} : la question d'équipe a disparu"
            )
            assert len(page.entries) == selection.PAGE_SIZE
            assert len(set(ids)) == len(ids), "une entrée servie deux fois"
            assert sum(1 for e in page.entries[:3] if e.encadrement) == 0, (
                "la tête reste au métier"
            )


def test_a_team_question_survives_having_seen_the_first_one() -> None:
    """Deuxième préparation : la suivante remonte, on ne retombe pas au tiroir."""
    management = [entry for entry in ALL_ENTRIES if entry.encadrement]
    first = selection.select("recruitment", encadrement=True)
    served = {e.id for e in first.entries} & {e.id for e in management}

    again = selection.select("recruitment", seen=served, encadrement=True)
    still = {e.id for e in again.entries} & {e.id for e in management}
    assert still and not (still & served)


def test_the_route_accepts_the_encadrement_flag() -> None:
    response = client.get("/v3/interview/bank?use_case_id=recruitment&encadrement=true")

    assert response.status_code == 200
    assert len(response.json()["questions"]) == selection.PAGE_SIZE


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


def test_a_review_is_not_a_technical_screening() -> None:
    """« Vendez-moi ce stylo » n'a rien à faire dans un entretien annuel.

    Les questions métier sont écrites pour évaluer une compétence en vue d'un
    poste. Servies dans un bilan — avec quelqu'un qui a suivi le travail toute
    l'année — elles prenaient les trois premières places d'une page de huit
    sans qu'aucune ait la moindre chance d'être posée.
    """
    bilans = set(selection.PLANS) - selection.TYPES_EVALUATION
    assert bilans == {"annual_review", "mid_year", "performance_review"}

    for use_case_id in sorted(bilans):
        for metier, source in selection.METIERS.items():
            page = selection.select(use_case_id, metier=metier)
            assert not ({e.id for e in page.entries} & {e.id for e in source}), (
                f"{use_case_id} : le métier {metier} s'invite dans un bilan"
            )
            assert len(page.entries) == selection.PAGE_SIZE

    # Là où une compétence est évaluée, la promesse des trois en tête tient.
    for use_case_id in sorted(selection.TYPES_EVALUATION):
        for metier, source in selection.METIERS.items():
            head = selection.select(use_case_id, metier=metier).entries[:3]
            assert all(e.id in {x.id for x in source} for e in head), (
                f"{use_case_id} + {metier} : la tête n'est plus au métier"
            )


def test_the_catalog_says_where_a_metier_applies() -> None:
    """L'app ne doit pas redeviner ce que le serveur sait déjà."""
    payload = client.get("/v3/interview/metiers").json()

    assert payload["applies_to"] == sorted(selection.TYPES_EVALUATION)
    assert set(payload["applies_to"]) <= set(selection.PLANS)
