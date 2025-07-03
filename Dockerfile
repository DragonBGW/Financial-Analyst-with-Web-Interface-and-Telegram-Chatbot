############################################
# 1️⃣  Base layer – common dependencies
############################################
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg   

WORKDIR /app

# Install system deps needed for many‑linux wheels (scipy, psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

# Use a build‑cache mount so subsequent builds are faster
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

############################################
# 2️⃣  Web service stage
############################################
FROM base AS web

# Copy project code AFTER deps so code changes don’t bust pip layer
COPY . .

# Default command for the web service
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

############################################
# 3️⃣  Bot service stage
############################################
FROM base AS bot

COPY . .

CMD ["python", "manage.py", "telegrambot"]
