from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "requalifications"

router = APIRouter()


class RequalificationCreate(BaseModel):
    name: str


class RequalificationUpdate(BaseModel):
    name: str | None = None


class RequalificationRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=RequalificationRecord, status_code=status.HTTP_201_CREATED)
def create_requalification(
    payload: RequalificationCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> RequalificationRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return RequalificationRecord(**record)


@router.get("", response_model=list[RequalificationRecord])
def list_requalifications(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[RequalificationRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [RequalificationRecord(**record) for record in records]


@router.get("/{requalification_id}", response_model=RequalificationRecord)
def get_requalification(
    requalification_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> RequalificationRecord:
    record = fetch_one(client, TABLE_NAME, requalification_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Requalification not found")
    return RequalificationRecord(**record)


@router.patch("/{requalification_id}", response_model=RequalificationRecord)
def update_requalification(
    requalification_id: str,
    payload: RequalificationUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> RequalificationRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, requalification_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="Requalification not found")
    return RequalificationRecord(**record)


@router.delete("/{requalification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_requalification(
    requalification_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, requalification_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Requalification not found")
    return None
