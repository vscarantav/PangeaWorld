"""Runtime configuration checks shared by startup and deployment tests."""

import os
from urllib.parse import urlparse


class ConfigurationError(RuntimeError):
    pass


def is_production() -> bool:
    return os.getenv("PANGEAWORLD_ENV", "development").strip().lower() == "production"


def validate_production_config() -> None:
    """Fail fast when a production service could lose data or expose secrets."""
    if not is_production():
        return

    required = (
        "PANGEAWORLD_DATABASE_URL",
        "PANGEAWORLD_MIGRATION_DATABASE_URL",
        "PANGEAWORLD_CORS_ORIGINS",
        "GEMINI_API_KEY",
        "GEMINI_ADVISOR_MODEL",
        "GEMINI_NEWS_MODEL",
    )
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise ConfigurationError(f"Missing production environment variables: {', '.join(missing)}")

    database_url = os.environ["PANGEAWORLD_DATABASE_URL"]
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ConfigurationError("Production requires a PostgreSQL PANGEAWORLD_DATABASE_URL")
    if "sslmode=require" not in database_url and "sslmode=verify-full" not in database_url:
        raise ConfigurationError("Production PostgreSQL must require TLS with sslmode=require or sslmode=verify-full")

    migration_url = os.environ["PANGEAWORLD_MIGRATION_DATABASE_URL"]
    if not migration_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ConfigurationError("Production migrations require a PostgreSQL PANGEAWORLD_MIGRATION_DATABASE_URL")
    if "-pooler." in migration_url:
        raise ConfigurationError("Production migrations must use Neon's direct, non-pooled connection URL")
    if "sslmode=require" not in migration_url and "sslmode=verify-full" not in migration_url:
        raise ConfigurationError("Production migration PostgreSQL must require TLS")

    origins = [item.strip() for item in os.environ["PANGEAWORLD_CORS_ORIGINS"].split(",") if item.strip()]
    if not origins or any(urlparse(origin).scheme != "https" for origin in origins):
        raise ConfigurationError("Production CORS origins must all use HTTPS")
    if os.getenv("PANGEAWORLD_COOKIE_SECURE") != "1":
        raise ConfigurationError("Production requires PANGEAWORLD_COOKIE_SECURE=1")
