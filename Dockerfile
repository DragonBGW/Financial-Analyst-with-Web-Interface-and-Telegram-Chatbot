# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PORT=8000

WORKDIR /app

# System packages (needed for psycopg2, PIL, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# For matplotlib PNG plot saving
RUN mkdir -p static/plots

EXPOSE 8000

# Default CMD = web app (overridden on Render for Telegram bot)
CMD ["gunicorn", "stockinsight.wsgi:application", "--bind", "0.0.0.0:${PORT}", "--timeout", "120"]
