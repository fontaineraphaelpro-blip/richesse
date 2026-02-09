web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile - --log-level info wsgi:application
worker: python src/main.py

