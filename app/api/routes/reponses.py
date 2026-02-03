from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "reponses_entretiens"

router = APIRouter()


class ReponseCreate(BaseModel):
    name: str


class ReponseUpdate(BaseModel):
    name: str | None = None


class ReponseRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=ReponseRecord, status_code=status.HTTP_201_CREATED)
def create_reponse(
    payload: ReponseCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ReponseRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return ReponseRecord(**record)


@router.get("", response_model=list[ReponseRecord])
def list_reponses(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[ReponseRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [ReponseRecord(**record) for record in records]


@router.get("/{reponse_id}", response_model=ReponseRecord)
def get_reponse(
    reponse_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ReponseRecord:
    record = fetch_one(client, TABLE_NAME, reponse_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ReponseEntretien not found")
    return ReponseRecord(**record)


@router.patch("/{reponse_id}", response_model=ReponseRecord)
def update_reponse(
    reponse_id: str,
    payload: ReponseUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ReponseRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, reponse_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="ReponseEntretien not found")
    return ReponseRecord(**record)


@router.delete("/{reponse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reponse(
    reponse_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, reponse_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ReponseEntretien not found")
    return None
