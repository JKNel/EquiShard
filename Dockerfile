# EquiShard - Multi-stage Dockerfile for Coolify deployment

# ============================================
# Stage 1: Base image with dependencies
# ============================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Stage 2: Builder stage for dependencies
# ============================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ============================================
# Stage 3: Production image
# ============================================
FROM base as production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
# Health check (Conditional: Pass if Worker, Check URL if Web)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$RUN_WORKER" = "true" ]; then exit 0; else python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1; fi

# Run script (Worker) or Server (Web) based on ENV
CMD ["/bin/bash", "-c", "if [ \"$RUN_WORKER\" = \"true\" ]; then echo 'Starting Worker...'; python manage.py price_fluctuation; else echo 'Starting Web App...'; exec gunicorn equishard.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile -; fi"]
