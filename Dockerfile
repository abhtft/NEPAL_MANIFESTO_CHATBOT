# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      curl \
      build-essential \
      git \
      && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for caching
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip wheel setuptools && \
    pip install -r /app/requirements.txt

# Copy app source
COPY . /app

# Ensure persistence directory exists
RUN mkdir -p /app/chroma_store && chmod -R 777 /app/chroma_store

# Streamlit defaults
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Default Azure version (override at run-time as needed)
ENV AZURE_OPENAI_API_VERSION=2024-02-01

# Make entrypoint executable
RUN sed -i 's/\r$//' /app/entrypoint.sh || true && \
    chmod +x /app/entrypoint.sh || true

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
