from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Legitima Backend"
    version: str = "0.1.0"


settings = Settings()
