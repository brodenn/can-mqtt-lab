FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir python-can requests paho-mqtt

# Copy the reader script (or entire dir if you expect logs or updates)
COPY . .

# Create logs directory (optional if not mapped via volume)
RUN mkdir -p logs

# Expose nothing (headless logger)
CMD ["python", "can_reader.py"]
