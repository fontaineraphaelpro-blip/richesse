web: python -c "import sys; sys.path.insert(0, 'src'); from web_app import app; import os; from gunicorn.app.wsgiapp import WSGIApplication; WSGIApplication('%(prog)s [OPTIONS] [APP_MODULE]', prog='gunicorn').run()" --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 wsgi:application
worker: python src/main.py

