# Railway: build avec image Python officielle (plus de dépendance à mise/Railpack)
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE $PORT

# Même commande que le Procfile
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile - wsgi:application
