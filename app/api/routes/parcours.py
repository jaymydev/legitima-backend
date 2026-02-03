from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "parcours_professionnels"

router = APIRouter()


class ParcoursCreate(BaseModel):
    name: str


class ParcoursUpdate(BaseModel):
    name: str | None = None


class ParcoursRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=ParcoursRecord, status_code=status.HTTP_201_CREATED)
def create_parcours(
    payload: ParcoursCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ParcoursRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return ParcoursRecord(**record)


@router.get("", response_model=list[ParcoursRecord])
def list_parcours(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[ParcoursRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [ParcoursRecord(**record) for record in records]


@router.get("/{parcours_id}", response_model=ParcoursRecord)
def get_parcours(
    parcours_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ParcoursRecord:
    record = fetch_one(client, TABLE_NAME, parcours_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ParcoursProfessionnel not found")
    return ParcoursRecord(**record)


@router.patch("/{parcours_id}", response_model=ParcoursRecord)
def update_parcours(
    parcours_id: str,
    payload: ParcoursUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ParcoursRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, parcours_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="ParcoursProfessionnel not found")
    return ParcoursRecord(**record)


@router.delete("/{parcours_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parcours(
    parcours_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, parcours_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ParcoursProfessionnel not found")
    return None
