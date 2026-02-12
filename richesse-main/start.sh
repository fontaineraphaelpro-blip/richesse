#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 120 --access-logfile - --error-logfile - wsgi:application
