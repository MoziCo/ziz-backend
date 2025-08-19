# Multi-stage Dockerfile for Ziz API
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry sync --only=main

# Production API stage
FROM base as api
COPY . .
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "ziz.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
