import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL


def resolve_database_url(database_url: str | None = None) -> str:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    explicit_url = database_url or os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["POSTGRES_DB"],
    ).render_as_string(hide_password=False)
