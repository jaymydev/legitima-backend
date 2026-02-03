import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Legitima Backend"
    version: str = "0.1.0"
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_anon_key: str | None = os.getenv("SUPABASE_ANON_KEY")


settings = Settings()
