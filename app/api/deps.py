from __future__ import annotations

from fastapi import Header, HTTPException
from supabase import Client, create_client
from typing import Optional

from app.config.settings import settings


def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_user_id(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header is required")
    return x_user_id
