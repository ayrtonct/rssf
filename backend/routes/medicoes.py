# routes/medicoes.py
from flask import Blueprint, request, jsonify
from models.medicao import MedicaoModel
import mysql.connector
from config import DB_CONFIG
from datetime import datetime, timedelta

medicoes_bp = Blueprint('medicoes', __name__)

@medicoes_bp.route('/api/salvar_dados', methods=['POST'])
def api_salvar_dados():
    try:
        data = request.get_json()
        if MedicaoModel.salvar(data):
            return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@medicoes_bp.route('/api/medicoes/<int:sensor_id>', methods=['GET'])
def get_medicoes(sensor_id):
    try:
        limite = request.args.get('limite', default=100, type=int)
        dados = MedicaoModel.get_por_sensor(sensor_id, limite)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@medicoes_bp.route('/api/medicoes', methods=['GET'])
def get_medicoes_periodo():
    try:
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        if not inicio or not fim:
            return jsonify({"error": "Parâmetros 'inicio' e 'fim' são obrigatórios."}), 400
        dados = MedicaoModel.get_por_periodo(inicio, fim)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@medicoes_bp.route('/api/medicoes/recentes', methods=['GET'])
def get_recentes():
    try:
        dados = MedicaoModel.get_recentes()
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@medicoes_bp.route('/api/status', methods=['GET'])
def get_status():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT sensor_id, MAX(created_at) as ultima_transmissao
            FROM medicoes
            GROUP BY sensor_id
        """)
        sensores = cursor.fetchall()

        agora = datetime.now()
        resultado = []

        for s in sensores:
            ultima = s['ultima_transmissao']
            
            if isinstance(ultima, (bytes, bytearray)):
                ultima = ultima.decode('utf-8')
            if isinstance(ultima, str):
                # O banco pode retornar string se use_pure=True
                try:
                    ultima = datetime.strptime(ultima, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ultima = datetime.strptime(ultima, "%Y-%m-%d %H:%M:%S.%f")

            delta  = agora - ultima
            minutos = int(delta.total_seconds() / 60)

            if delta < timedelta(hours=1):
                status = "online"
            elif delta < timedelta(hours=3):
                status = "instavel"
            else:
                status = "offline"

            resultado.append({
                "sensor_id":           s['sensor_id'],
                "ultima_transmissao":  ultima.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ultima, 'strftime') else str(ultima),
                "status":              status,
                "minutos_desde_ultima": minutos
            })

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            if cursor: cursor.close()
            conn.close()
