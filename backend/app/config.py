import os
from pathlib import Path
from typing import Optional


class Settings:
    NEBIUS_API_KEY: Optional[str] = os.getenv("NEBIUS_API_KEY")
    NEBIUS_BASE_URL: Optional[str] = os.getenv(
        "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
    )
    NEBIUS_MODEL: Optional[str] = os.getenv(
        "NEBIUS_MODEL", "nvidia/Nemotron-3-Ultra-550b-a55b"
    )
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # OpenAI-compatible model name for Nebius
    # Can be overridden via NEBIUS_MODEL env var
    DEFAULT_MODEL: str = NEBIUS_MODEL or "nvidia/Nemotron-3-Ultra-550b-a55b"

    # Whether to use HTTP or HTTPS
    VERIFY_SSL: bool = True

    # API timeout in seconds
    API_TIMEOUT: int = 60

    # Repository scanning settings
    MAX_REPO_SIZE_MB: int = 100
    MAX_FILE_SIZE_KB: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
