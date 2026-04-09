# routes/medicoes.py
from flask import Blueprint, request, jsonify
from models.medicao import MedicaoModel

medicoes_bp = Blueprint('medicoes', __name__)

@medicoes_bp.route('/api/salvar_dados', methods=['POST'])
def api_salvar_dados():
    try:
        data = request.get_json()
        if MedicaoModel.salvar(data):
            return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
