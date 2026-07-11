from __future__ import annotations

from typing import Optional

from supabase import Client

from app.observability.logging import logger


def fetch_list(client: Client, table_name: str, user_id: str) -> list[dict]:
    try:
        response = client.table(table_name).select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as exc:
        logger.exception(
            "Supabase operation failed",
            extra={"operation": "fetch_list", "table": table_name},
        )
        raise


def fetch_one(client: Client, table_name: str, record_id: str, user_id: str) -> Optional[dict]:
    try:
        response = (
            client.table(table_name)
            .select("*")
            .eq("id", record_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.exception(
            "Supabase operation failed",
            extra={"operation": "fetch_one", "table": table_name},
        )
        raise


def insert_one(client: Client, table_name: str, payload: dict) -> dict:
    try:
        response = client.table(table_name).insert(payload).execute()
        return response.data[0]
    except Exception as exc:
        logger.exception(
            "Supabase operation failed",
            extra={"operation": "insert_one", "table": table_name},
        )
        raise


def update_one(
    client: Client,
    table_name: str,
    record_id: str,
    user_id: str,
    payload: dict,
) -> Optional[dict]:
    try:
        response = (
            client.table(table_name)
            .update(payload)
            .eq("id", record_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.exception(
            "Supabase operation failed",
            extra={"operation": "update_one", "table": table_name},
        )
        raise


def delete_one(client: Client, table_name: str, record_id: str, user_id: str) -> Optional[dict]:
    try:
        response = (
            client.table(table_name)
            .delete()
            .eq("id", record_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.exception(
            "Supabase operation failed",
            extra={"operation": "delete_one", "table": table_name},
        )
        raise
