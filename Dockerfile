# syntax=docker/dockerfile:1
###############################################################################
#  Stock‑Insight Dockerfile  –  simple COPY . .
###############################################################################

FROM python:3.12-slim

# ─── Runtime env vars ────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PORT=8000

WORKDIR /app

# ─── System deps (for psycopg2‑binary, Pillow, etc.) ─────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ─── Python deps first (leverages layer cache) ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# ─── Copy the entire repo (everything else) ──────────────────────────────────
COPY . .

# Ensure entrypoint executable (in case git lost +x)
RUN chmod +x ./entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
