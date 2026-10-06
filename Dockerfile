# =============================================================================
# Enterprise SaaS Backend Dockerfile - Haki FMCG 2.0 / Haki Procure AI
# Multi-stage, non-root security container
# =============================================================================

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Runtime Environment
FROM python:3.11-slim AS runtime

# Install system runtime dependencies for PDF & OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 10001 -s /sbin/nologin appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Copy application source code
COPY --chown=appuser:appgroup . /app

# Ensure uploads directory exists and is writable by appuser
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app/uploads

# Switch to non-root user
USER appuser

EXPOSE 8000

# Enterprise healthcheck via liveness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/healthz || exit 1

# Default command: FastAPI production server
CMD ["uvicorn", "api.rest_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
