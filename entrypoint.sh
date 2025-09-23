#!/usr/bin/env sh
set -e

# Map env var names used in code
# Prefer AZURE_OPENAI_ENDPOINT but code may read AZURE_ENDPOINT
#not good code

if [ -n "$AZURE_OPENAI_ENDPOINT" ] && [ -z "$AZURE_ENDPOINT" ]; then
  export AZURE_ENDPOINT="$AZURE_OPENAI_ENDPOINT"
fi

# Ensure chroma_store exists
mkdir -p /app/chroma_store

# Run ingestion only if store appears empty
if [ -z "$(ls -A /app/chroma_store 2>/dev/null)" ]; then
  echo "[entrypoint] Chroma store empty. Running ingestion..."
  python /app/ingest/ingest.py || {
    echo "[entrypoint] Ingestion failed" >&2
    exit 1
  }
else
  echo "[entrypoint] Chroma store already populated. Skipping ingestion."
fi

# Launch Streamlit
exec streamlit run /app/app.py --server.port ${STREAMLIT_SERVER_PORT:-8501} --server.address ${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}

docker run -p 8501:8501 manifesto-chatbot:latest
