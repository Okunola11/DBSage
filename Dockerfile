# Base stage for both dev and production
FROM python:3.12.6-slim-bullseye AS base

WORKDIR /usr/src

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Poetry's configuration:
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=1.8.3 


# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only Poetry-related files to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Development stage
FROM base AS dev

# Install additional dev tools
RUN poetry add debugpy

RUN poetry install --no-root

COPY . .

CMD ["uvicorn", "db_sage.main:app", "--host", "0.0.0.0", "--port", "7002", "--reload"]

# Production build stage
FROM base AS production

ENV FASTAPI_ENV=production

# Add production dependencies
RUN poetry add gunicorn python-multipart

# Install all dependencies including the newly added ones
RUN poetry install --no-root --no-dev

RUN useradd -u 1001 -s /bin/bash nonroot

RUN chown -R nonroot /usr/src

# Using non-root user
USER nonroot

# Copy only required files
COPY ./db_sage /usr/src/db_sage

EXPOSE 7002

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "db_sage.main:app", "--bind", "0.0.0.0:7002"]