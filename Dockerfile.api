FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY public_intake_api.py intake_store.py ./
COPY schemas ./schemas
CMD exec gunicorn --bind :${PORT} --workers 2 --threads 4 --timeout 0 public_intake_api:app
