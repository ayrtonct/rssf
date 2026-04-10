# app.py
import os
from flask import Flask
from routes.medicoes import medicoes_bp

app = Flask(__name__)

# Registrar as rotas
app.register_blueprint(medicoes_bp)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
