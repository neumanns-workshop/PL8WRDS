# Multi-stage Dockerfile for PL8WRDS FastAPI Application
# Production-optimized with security best practices

# Build Arguments
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# ================================
# Stage 1: Base Python Image
# ================================
FROM python:${PYTHON_VERSION}-slim as base

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ================================
# Stage 2: Build Dependencies
# ================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ================================
# Stage 3: Runtime Image
# ================================
FROM base as runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r pl8wrds && useradd -r -g pl8wrds -s /bin/false pl8wrds

# Create application directories
RUN mkdir -p /app /app/cache /app/data /app/models /app/logs && \
    chown -R pl8wrds:pl8wrds /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=pl8wrds:pl8wrds app/ /app/app/
COPY --chown=pl8wrds:pl8wrds run_scoring.py /app/
COPY --chown=pl8wrds:pl8wrds pytest.ini /app/

# Copy data files if they exist
COPY --chown=pl8wrds:pl8wrds data/ /app/data/ 2>/dev/null || true

# Create cache and data directories with proper permissions
RUN touch /app/data/words_with_freqs.json \
    /app/cache/corpus_stats.json \
    /app/cache/corpus_features.json && \
    chown -R pl8wrds:pl8wrds /app/cache /app/data /app/models /app/logs

# Switch to non-root user
USER pl8wrds

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Add metadata labels
LABEL maintainer="PL8WRDS Team" \
    org.opencontainers.image.title="PL8WRDS API" \
    org.opencontainers.image.description="License plate word scoring API built with FastAPI" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${VCS_REF}" \
    org.opencontainers.image.source="https://github.com/username/PL8WRDS" \
    org.opencontainers.image.licenses="MIT"

# Default command - run with gunicorn for production
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info"]

# ================================
# Stage 4: Development Image
# ================================
FROM runtime as development

# Switch back to root for development setup
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    watchdog[watchmedo] \
    ipython \
    ipdb \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    ruff \
    mypy

# Copy test files
COPY --chown=pl8wrds:pl8wrds tests/ /app/tests/

# Switch back to non-root user
USER pl8wrds

# Development command - run with uvicorn reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ================================
# Stage 5: Testing Image
# ================================
FROM development as testing

# Switch to root for test setup
USER root

# Install additional testing tools
RUN pip install --no-cache-dir \
    locust \
    pytest-benchmark \
    pytest-xdist \
    coverage[toml]

# Switch back to non-root user
USER pl8wrds

# Testing command
CMD ["pytest", "tests/", "-v", "--cov=app", "--cov-report=term-missing", "--cov-report=html"]

# ================================
# Final Production Image
# ================================
FROM runtime as production

# Ensure we're using the non-root user
USER pl8wrds

# Production-specific optimizations
ENV PYTHONOPTIMIZE=2

# Add gunicorn to runtime image
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

# Final production command with optimized settings
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--worker-connections", "1000", \
     "--bind", "0.0.0.0:8000", \
     "--keep-alive", "2", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--capture-output"]