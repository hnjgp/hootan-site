from app.config import Settings


def test_environment_overrides_env_file(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@example:5432/x")
    settings = Settings()
    assert settings.database_url == "postgresql+asyncpg://u:p@example:5432/x"
