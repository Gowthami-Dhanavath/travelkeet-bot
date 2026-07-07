# Multi-stage Python 3.11 build for the TravelKeet AI trip planner.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: build-essential for asyncpg wheel fallback, libpq-dev for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# App code
COPY app ./app
COPY prompts ./prompts
COPY data ./data
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8000

# Migrations run at container start, then uvicorn.
# Railway's startCommand in railway.json takes precedence in cloud;
# this CMD keeps `docker run` viable for local prod-parity testing.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 75"]