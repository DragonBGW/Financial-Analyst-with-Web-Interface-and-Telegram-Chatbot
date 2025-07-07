# syntax=docker/dockerfile:1
###############################################################################
#  Stock‑Insight Dockerfile
#  • Builds a single image for both Django web service (default CMD)
#    and Telegram bot worker (override CMD on Render).
###############################################################################

FROM python:3.12-slim

# ────────────────────────────
# Environment configuration
# ────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PORT=8000

WORKDIR /app

# ────────────────────────────
# System packages needed by many‑linux wheels (psycopg2‑binary, Pillow, etc.)
# ────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ────────────────────────────
# Python dependencies (layer‑cache friendly)
# ────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# ────────────────────────────
# Copy project source
# ────────────────────────────
COPY . .

# Create directory for saved matplotlib plots (optional)
RUN mkdir -p static/plots

# ────────────────────────────
# Expose port for local docker run (Render ignores EXPOSE for binding)
# ────────────────────────────
EXPOSE 8000

# ────────────────────────────
# Default command: production web server
# (Uses `sh -c` so $PORT is expanded at runtime)
# ────────────────────────────
CMD ["sh", "-c", "gunicorn stockinsight.wsgi:application --bind 0.0.0.0:$PORT --timeout 120"]
