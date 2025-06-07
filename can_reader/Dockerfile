FROM python:3.11-slim

WORKDIR /app

COPY can_reader.py .

RUN pip install --no-cache-dir python-can requests paho-mqtt

CMD ["python", "can_reader.py"]
