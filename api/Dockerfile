FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies early for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Flask port
EXPOSE 5000

# Start the Flask + SocketIO app
CMD ["python", "app.py"]
