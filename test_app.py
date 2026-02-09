"""
Application Flask minimale pour tester le démarrage.
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>✅ Test réussi !</h1><p>Le serveur Flask fonctionne.</p>"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Test app works"}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

