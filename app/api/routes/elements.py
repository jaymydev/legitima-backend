from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_supabase_client, get_user_id
from app.persistence.supabase import delete_one, fetch_list, fetch_one, insert_one, update_one

TABLE_NAME = "elements_de_parcours"

router = APIRouter()


class ElementCreate(BaseModel):
    name: str


class ElementUpdate(BaseModel):
    name: str | None = None


class ElementRecord(BaseModel):
    id: str
    user_id: str
    name: str


@router.post("", response_model=ElementRecord, status_code=status.HTTP_201_CREATED)
def create_element(
    payload: ElementCreate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ElementRecord:
    record = insert_one(
        client,
        TABLE_NAME,
        {"user_id": user_id, "name": payload.name},
    )
    return ElementRecord(**record)


@router.get("", response_model=list[ElementRecord])
def list_elements(
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[ElementRecord]:
    records = fetch_list(client, TABLE_NAME, user_id)
    return [ElementRecord(**record) for record in records]


@router.get("/{element_id}", response_model=ElementRecord)
def get_element(
    element_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ElementRecord:
    record = fetch_one(client, TABLE_NAME, element_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ElementDeParcours not found")
    return ElementRecord(**record)


@router.patch("/{element_id}", response_model=ElementRecord)
def update_element(
    element_id: str,
    payload: ElementUpdate,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> ElementRecord:
    update_payload = payload.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    record = update_one(client, TABLE_NAME, element_id, user_id, update_payload)
    if not record:
        raise HTTPException(status_code=404, detail="ElementDeParcours not found")
    return ElementRecord(**record)


@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_element(
    element_id: str,
    user_id: str = Depends(get_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    record = delete_one(client, TABLE_NAME, element_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="ElementDeParcours not found")
    return None
