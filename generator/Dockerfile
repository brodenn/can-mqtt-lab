FROM python:3.11-slim

# Ensure real-time logs, better for Docker
ENV PYTHONUNBUFFERED=1  

# Set working directory
WORKDIR /app

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Default to running main.py (but easy to override)
CMD ["python", "main.py"]
