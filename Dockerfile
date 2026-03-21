FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (excluding .env)
COPY backend/ ./backend/
COPY backend/.env.example ./backend/.env  # Use example as template

# Copy frontend files
COPY frontend/ ./frontend/
COPY frontend/ ./backend/frontend/

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Start with the script
CMD ["./start.sh"]
