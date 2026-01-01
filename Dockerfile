# The Undertow API Dockerfile
# Multi-stage build for optimized production image

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN poetry export -f requirements.txt --without-hashes | pip install -r /dev/stdin

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 undertow && \
    chown -R undertow:undertow /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=undertow:undertow src/ /app/src/
COPY --chown=undertow:undertow migrations/ /app/migrations/
COPY --chown=undertow:undertow prompts/ /app/prompts/

# Set Python path
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER undertow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command
CMD ["uvicorn", "undertow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

