# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PORT=8000

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# ─── App source (ONLY paths that really exist) ─────────────────────
COPY entrypoint.sh         ./entrypoint.sh
COPY manage.py             ./manage.py
COPY stock_prediction_main ./stock_prediction_main
COPY core                  ./core
COPY templates             ./templates
COPY static                ./static
# Add more COPY lines only if the folder exists:
# COPY users               ./users
# COPY api                 ./api

RUN chmod +x ./entrypoint.sh
EXPOSE 8000
CMD ["./entrypoint.sh"]
