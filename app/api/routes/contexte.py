from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "contexte_entretiens"

router = APIRouter()


class ContexteCreate(BaseModel):
    name: str


class ContexteUpdate(BaseModel):
    name: str | None = None


class ContexteRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=ContexteRecord, status_code=status.HTTP_201_CREATED)
def create_contexte(
    payload: ContexteCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ContexteRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return ContexteRecord(**record)


@router.get("", response_model=list[ContexteRecord])
def list_contexte(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[ContexteRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [ContexteRecord(**record) for record in records]


@router.get("/{contexte_id}", response_model=ContexteRecord)
def get_contexte(
    contexte_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ContexteRecord:
    record = fetch_one(client, TABLE_NAME, contexte_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ContexteEntretien not found")
    return ContexteRecord(**record)


@router.patch("/{contexte_id}", response_model=ContexteRecord)
def update_contexte(
    contexte_id: str,
    payload: ContexteUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ContexteRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, contexte_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="ContexteEntretien not found")
    return ContexteRecord(**record)


@router.delete("/{contexte_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contexte(
    contexte_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, contexte_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ContexteEntretien not found")
    return None
