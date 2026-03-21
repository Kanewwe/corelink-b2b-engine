FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (without .env - use .env.example instead)
COPY backend/ ./backend/

# Copy frontend files
COPY frontend/ ./frontend/
COPY frontend/ ./backend/frontend/

# Use .env.example as template
RUN if [ -f backend/.env.example ]; then cp backend/.env.example backend/.env; fi

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
