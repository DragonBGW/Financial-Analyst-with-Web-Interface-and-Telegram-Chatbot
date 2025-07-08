# syntax=docker/dockerfile:1
###############################################################################
#  Stock‑Insight Dockerfile (explicit COPY – no COPY . .)
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
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# ─── Copy only what the app needs (adjust paths to fit your repo) ────────────
COPY entrypoint.sh          ./entrypoint.sh
COPY manage.py              ./manage.py
COPY stock_prediction_main  ./stock_prediction_main    # Django project pkg
COPY core                   ./core                     # your custom app
COPY templates              ./templates                # Jinja/Django templates
COPY static                 ./static                   # static assets

# If you have additional Django apps, add more COPY lines like:
# COPY users ./users
# COPY api   ./api

# ─── Ensure entrypoint is executable ────────────────────────────────────────
RUN chmod +x ./entrypoint.sh

# ─── Open the service port (helpful for local docker run) ───────────────────
EXPOSE 8000

# ─── Container startup ──────────────────────────────────────────────────────
CMD ["./entrypoint.sh"]
