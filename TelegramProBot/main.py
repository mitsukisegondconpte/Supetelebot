from app import app

if __name__ == '__main__':
    # Démarrer l'application avec gunicorn (via workflow)
    app.run(host='0.0.0.0', port=5000, debug=True)
