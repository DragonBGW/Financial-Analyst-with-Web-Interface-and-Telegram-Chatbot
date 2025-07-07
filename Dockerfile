############################################
# syntax=docker/dockerfile:1               #
############################################

############################################
# 1️⃣  Base layer – common dependencies
############################################
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

# System packages for many‑linux wheels (psycopg2, scipy, Pillow, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (leverages Docker layer cache)
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt


############################################
# 2️⃣  Web service stage
############################################
FROM base AS web

COPY . .

# Ensure directory for generated PNG plots
RUN mkdir -p static/plots

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


############################################
# 3️⃣  Bot service stage
############################################
FROM base AS bot

COPY . .

RUN mkdir -p static/plots

CMD ["python", "manage.py", "telegrambot"]
