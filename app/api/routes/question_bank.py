# Deliberately no `from __future__ import annotations` — see the note in the
# interview_questions router.

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel

from app.api.errors import UNKNOWN_USE_CASE, user_facing_error
from app.observability.logging import logger
from app.services.bank_selection import METIERS, PAGE_SIZE, select

router = APIRouter(prefix="/v3/interview", tags=["Question bank V3"])

#: Une page de garde sur la longueur de l'historique envoyé par le client.
MAX_SEEN = 200


class BankQuestion(BaseModel):
    id: str
    question: str
    answer: str
    follow_up: str = ""
    avoid: str = ""


class BankPage(BaseModel):
    use_case_id: str
    questions: list[BankQuestion]


@router.get("/bank", response_model=BankPage)
def get_bank_page(
    request: Request,
    response: Response,
    use_case_id: str,
    metier: str = "",
    seen: str = Query("", description="Identifiants déjà servis, séparés par des virgules"),
) -> BankPage:
    """Les questions à préparer, prises dans la banque écrite à la main.

    Aucun appel modèle : la réponse est instantanée, ne coûte rien, et ne dépend
    d'aucun fournisseur. C'est ce qui permet de servir une page utile à quelqu'un
    qui n'a rien saisi — le cas que la génération ne savait pas traiter autrement
    qu'en inventant un parcours.

    Les gabarits partent avec leurs balises intactes : ils sont remplis sur
    l'appareil, pour que ce que la personne écrit — son salaire, notamment — n'ait
    jamais besoin de quitter son téléphone.
    """
    del request, response

    seen_ids = {item for item in seen.split(",") if item}
    if len(seen_ids) > MAX_SEEN:
        seen_ids = set(list(seen_ids)[:MAX_SEEN])

    selection = select(use_case_id, seen=seen_ids, metier=metier or None)
    if selection is None:
        raise user_facing_error(UNKNOWN_USE_CASE)

    logger.info(
        "Bank page served use_case_id=%s metier=%s seen_count=%d question_count=%d",
        use_case_id,
        metier or "-",
        len(seen_ids),
        len(selection.entries),
    )
    return BankPage(
        use_case_id=selection.use_case_id,
        questions=[BankQuestion(**vars(entry)) for entry in selection.entries],
    )


class MetierCatalog(BaseModel):
    metiers: list[str]


@router.get("/metiers", response_model=MetierCatalog)
def get_metiers() -> MetierCatalog:
    return MetierCatalog(metiers=sorted(METIERS))
