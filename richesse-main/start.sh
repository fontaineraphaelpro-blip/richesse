#!/bin/bash
# Script de démarrage pour Railpack

set -e

echo "🚀 Démarrage du serveur crypto signal scanner..."

# Obtenir le port dynamiquement
PORT=${PORT:-8000}

# Lancer Gunicorn avec WSGI
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:application
