FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

COPY alembic.ini ./
COPY alembic ./alembic

RUN python -c "from fastapi.testclient import TestClient; from dota_tracker.presentation.web.app import app; client = TestClient(app); assert all(client.get(path).status_code == 200 for path in ('/', '/app.js', '/styles.css'))" \
    && DATABASE_URL='postgresql+psycopg2://user:p%25ass@localhost/db' alembic upgrade head --sql > /dev/null

CMD ["python", "-m", "dota_tracker.presentation.web.container"]
