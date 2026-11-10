"""Start the containerized web app against the Compose PostgreSQL service."""

from __future__ import annotations

import os

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import URL


def main() -> None:
    """Configure the container database, migrate it, and replace this process with Uvicorn."""
    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DB_HOST")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required container settings: {', '.join(missing)}")

    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )
    # Override the host's DATABASE_URL for both Alembic and the web process.
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    command.upgrade(Config("alembic.ini"), "head")
    os.execvp(
        "uvicorn",
        ["uvicorn", "dota_tracker.presentation.web.app:app", "--host", "0.0.0.0", "--port", "8000"],
    )


if __name__ == "__main__":
    main()
