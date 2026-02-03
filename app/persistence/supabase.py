from supabase import Client


def fetch_list(client: Client, table_name: str, user_id: str) -> list[dict]:
    response = client.table(table_name).select("*").eq("user_id", user_id).execute()
    return response.data or []


def fetch_one(client: Client, table_name: str, record_id: str, user_id: str) -> dict | None:
    response = (
        client.table(table_name)
        .select("*")
        .eq("id", record_id)
        .eq("user_id", user_id)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def insert_one(client: Client, table_name: str, payload: dict) -> dict:
    response = client.table(table_name).insert(payload).execute()
    return response.data[0]


def update_one(
    client: Client,
    table_name: str,
    record_id: str,
    user_id: str,
    payload: dict,
) -> dict | None:
    response = (
        client.table(table_name)
        .update(payload)
        .eq("id", record_id)
        .eq("user_id", user_id)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def delete_one(client: Client, table_name: str, record_id: str, user_id: str) -> dict | None:
    response = (
        client.table(table_name)
        .delete()
        .eq("id", record_id)
        .eq("user_id", user_id)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None
