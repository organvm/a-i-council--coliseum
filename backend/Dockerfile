FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy MVP requirements and install Python dependencies
COPY backend/requirements-test.txt /app/backend/requirements-test.txt
RUN pip install --no-cache-dir -r /app/backend/requirements-test.txt

# Copy application code
COPY backend /app/backend

ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
