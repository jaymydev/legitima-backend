from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "zones_sensibles"

router = APIRouter()


class ZoneCreate(BaseModel):
    name: str


class ZoneUpdate(BaseModel):
    name: str | None = None


class ZoneRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=ZoneRecord, status_code=status.HTTP_201_CREATED)
def create_zone(
    payload: ZoneCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ZoneRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return ZoneRecord(**record)


@router.get("", response_model=list[ZoneRecord])
def list_zones(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[ZoneRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [ZoneRecord(**record) for record in records]


@router.get("/{zone_id}", response_model=ZoneRecord)
def get_zone(
    zone_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ZoneRecord:
    record = fetch_one(client, TABLE_NAME, zone_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ZoneSensible not found")
    return ZoneRecord(**record)


@router.patch("/{zone_id}", response_model=ZoneRecord)
def update_zone(
    zone_id: str,
    payload: ZoneUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ZoneRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, zone_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="ZoneSensible not found")
    return ZoneRecord(**record)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, zone_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ZoneSensible not found")
    return None
