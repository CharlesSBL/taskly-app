import pytest

from app.core.config import resolve_database_url

ENV_DATABASE_URL = "postgresql+psycopg://env-user:env-pass@env-host:5432/env-db"
POSTGRES_SETTINGS = {
    "POSTGRES_USER": "taskly",
    "POSTGRES_PASSWORD": "s3cret",
    "POSTGRES_HOST": "db.internal",
    "DB_PORT": "5433",
    "POSTGRES_DB": "taskly_test",
}
EXPECTED_GENERATED_URL = "postgresql+psycopg://taskly:s3cret@db.internal:5433/taskly_test"


@pytest.fixture
def postgres_settings(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for name, value in POSTGRES_SETTINGS.items():
        monkeypatch.setenv(name, value)
    return monkeypatch


def test_explicit_database_url_wins_over_the_environment(postgres_settings):
    postgres_settings.setenv("DATABASE_URL", ENV_DATABASE_URL)

    resolved = resolve_database_url("postgresql+psycopg://explicit:secret@host:5432/db")

    assert resolved == "postgresql+psycopg://explicit:secret@host:5432/db"


@pytest.mark.parametrize("database_url", [None, ""])
def test_environment_database_url_is_used_when_no_explicit_url(postgres_settings, database_url):
    postgres_settings.setenv("DATABASE_URL", ENV_DATABASE_URL)

    assert resolve_database_url(database_url) == ENV_DATABASE_URL


def test_generates_a_psycopg_url_from_the_postgres_settings(postgres_settings):
    assert resolve_database_url() == EXPECTED_GENERATED_URL


@pytest.mark.parametrize("missing", sorted(POSTGRES_SETTINGS))
def test_missing_postgres_setting_raises_key_error(postgres_settings, missing):
    postgres_settings.delenv(missing)

    with pytest.raises(KeyError, match=missing):
        resolve_database_url()
