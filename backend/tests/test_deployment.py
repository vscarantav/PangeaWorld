import pytest
from fastapi.testclient import TestClient

from config import ConfigurationError, validate_production_config
from main import app


PRODUCTION_ENV = {
    "PANGEAWORLD_ENV": "production",
    "PANGEAWORLD_DATABASE_URL": "postgresql+psycopg://user:password@host/database?sslmode=require",
    "PANGEAWORLD_MIGRATION_DATABASE_URL": "postgresql+psycopg://user:password@direct-host/database?sslmode=require",
    "PANGEAWORLD_CORS_ORIGINS": "https://pangeaworld.onrender.com",
    "PANGEAWORLD_COOKIE_SECURE": "1",
    "GEMINI_API_KEY": "test-key",
    "GEMINI_ADVISOR_MODEL": "test-advisor-model",
    "GEMINI_NEWS_MODEL": "test-news-model",
}


def test_healthz_checks_database():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_production_configuration_accepts_neon_shape(monkeypatch):
    for name, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(name, value)
    validate_production_config()


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("PANGEAWORLD_DATABASE_URL", "sqlite:///unsafe.db", "PostgreSQL"),
        ("PANGEAWORLD_DATABASE_URL", "postgresql+psycopg://host/database", "require TLS"),
        ("PANGEAWORLD_MIGRATION_DATABASE_URL", "postgresql+psycopg://host-pooler.example/database?sslmode=require", "direct"),
        ("PANGEAWORLD_CORS_ORIGINS", "http://pangeaworld.onrender.com", "HTTPS"),
        ("PANGEAWORLD_COOKIE_SECURE", "0", "COOKIE_SECURE"),
        ("GEMINI_API_KEY", "", "GEMINI_API_KEY"),
    ],
)
def test_production_configuration_rejects_unsafe_values(monkeypatch, name, value, message):
    for env_name, env_value in PRODUCTION_ENV.items():
        monkeypatch.setenv(env_name, env_value)
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError, match=message):
        validate_production_config()
