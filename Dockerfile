# Clinical Notes Summarizer - Production Dockerfile
# Healthcare-compliant container image with security and safety measures

# Multi-stage build for optimized production image
FROM python:3.9-slim-bullseye as builder

# Set build-time metadata
LABEL maintainer="Clinical Notes Summarizer Team"
LABEL version="1.0.0"
LABEL description="FHIR R4 compatible API for patient-friendly clinical summaries"
LABEL healthcare.compliance="HIPAA-aware"
LABEL healthcare.phi-storage="disabled"

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment for isolated dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better Docker layer caching
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.9-slim-bullseye as production

# Security: Create non-root user for healthcare compliance
RUN groupadd -r clinical && useradd -r -g clinical -u 1001 clinical

# Install runtime dependencies and security updates
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=clinical:clinical . /app/

# Healthcare Security: Ensure no sensitive files are included
RUN rm -rf .env* .git* docker-compose*.yml \
    && find /app -name "*.pyc" -delete \
    && find /app -name "__pycache__" -type d -exec rm -rf {} + || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/cache /app/temp \
    && chown -R clinical:clinical /app

# Security: Remove unnecessary packages and clean package manager cache
RUN apt-get autoremove -y && apt-get autoclean

# Healthcare Compliance: Set environment variables for production
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CLINICAL_ENVIRONMENT=production
ENV CLINICAL_DEBUG=false
ENV CLINICAL_ENABLE_PHI_PROTECTION=true
ENV CLINICAL_ENABLE_REQUEST_LOGGING=false
ENV CLINICAL_LOG_LEVEL=INFO
ENV CLINICAL_HOST=0.0.0.0
ENV CLINICAL_PORT=8000

# Healthcare Security: Disable unnecessary services and set secure defaults
ENV CLINICAL_ALLOWED_HOSTS="*"
ENV CLINICAL_RATE_LIMIT_PER_MINUTE=120
ENV CLINICAL_MAX_PROCESSING_TIME_SECONDS=5.0
ENV CLINICAL_MAX_REQUEST_SIZE_MB=10

# Expose port (documentation only, actual binding in docker-compose)
EXPOSE 8000

# Copy and make startup script executable
COPY --chown=clinical:clinical docker/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Switch to non-root user for security
USER clinical

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Use startup script as entrypoint for healthcare safety checks
ENTRYPOINT ["/app/startup.sh"]

# Default command to run the FastAPI application
CMD ["python", "-c", "import uvicorn; uvicorn.run('src.api.main:app', host='0.0.0.0', port=8000, workers=1, access_log=False)"]

# Production image metadata for healthcare compliance
LABEL healthcare.security.non-root="true"
LABEL healthcare.security.phi-protection="enabled"
LABEL healthcare.compliance.fhir="R4"
LABEL healthcare.deployment.ready="true"