FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend files to both possible locations
COPY frontend/ ./frontend/
COPY frontend/ ./backend/frontend/

# Set working directory to backend for uvicorn
WORKDIR /app/backend

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
