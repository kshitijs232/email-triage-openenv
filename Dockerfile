# Dockerfile for Email Triage Environment
# For HuggingFace Spaces deployment
#
# Build from repo root: docker build -t email-triage-env -f examples/email_triage_env/Dockerfile .
# Or standalone:        cd examples/email_triage_env && docker build -t email-triage-env .
# Run:                  docker run -p 8000:8000 email-triage-env

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install dependencies
# Detect if we're building from repo root or standalone and adjust paths
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f "pyproject.toml" ] && [ -d "src/openenv" ]; then \
        echo "Building from repo root - installing openenv-core"; \
        pip install --no-cache-dir -e .; \
        pip install --no-cache-dir -r examples/email_triage_env/requirements.txt; \
    elif [ -f "requirements.txt" ]; then \
        echo "Building standalone"; \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "ERROR: Cannot find requirements.txt"; \
        exit 1; \
    fi

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/src:/app/examples/email_triage_env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set working directory to the environment
WORKDIR /app/examples/email_triage_env

# Run the server
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
