# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels \
    && adduser --disabled-password --gecos "" appuser

COPY apps ./apps
RUN mkdir -p /app/apps/api/uploads \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "apps.api.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
