#!/bin/bash

# Generate .env from environment variables at runtime
cat > /app/backend/.env << ENVEOF
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-changeme}
API_TOKEN=${API_TOKEN:-secure-token-change-me}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
DATABASE_URL=${DATABASE_URL:-sqlite:///./corelink.db}
ENVEOF

echo "Generated .env with:"
cat /app/backend/.env

# Start uvicorn
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
