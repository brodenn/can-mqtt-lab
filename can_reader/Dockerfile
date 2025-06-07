FROM python:3.11-slim

WORKDIR /app

COPY can_reader.py .

RUN pip install python-can requests

CMD ["python", "can_reader.py"]
