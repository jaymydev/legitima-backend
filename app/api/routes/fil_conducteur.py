from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "fils_conducteurs"

router = APIRouter()


class FilConducteurCreate(BaseModel):
    name: str


class FilConducteurUpdate(BaseModel):
    name: str | None = None


class FilConducteurRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=FilConducteurRecord, status_code=status.HTTP_201_CREATED)
def create_fil_conducteur(
    payload: FilConducteurCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> FilConducteurRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return FilConducteurRecord(**record)


@router.get("", response_model=list[FilConducteurRecord])
def list_fil_conducteurs(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[FilConducteurRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [FilConducteurRecord(**record) for record in records]


@router.get("/{fil_conducteur_id}", response_model=FilConducteurRecord)
def get_fil_conducteur(
    fil_conducteur_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> FilConducteurRecord:
    record = fetch_one(client, TABLE_NAME, fil_conducteur_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="FilConducteur not found")
    return FilConducteurRecord(**record)


@router.patch("/{fil_conducteur_id}", response_model=FilConducteurRecord)
def update_fil_conducteur(
    fil_conducteur_id: str,
    payload: FilConducteurUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> FilConducteurRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, fil_conducteur_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="FilConducteur not found")
    return FilConducteurRecord(**record)


@router.delete("/{fil_conducteur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fil_conducteur(
    fil_conducteur_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, fil_conducteur_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="FilConducteur not found")
    return None
