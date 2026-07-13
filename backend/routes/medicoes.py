# routes/medicoes.py
import re
from flask import Blueprint, request, jsonify
from models.medicao import MedicaoModel
import mysql.connector
from config import DB_CONFIG, DEFAULT_GATEWAY_ID
from datetime import datetime, timedelta

medicoes_bp = Blueprint('medicoes', __name__)

def is_valid_gateway_id(val):
    if not val or not isinstance(val, str): return False
    val = val.strip()
    if len(val) == 0 or len(val) > 64: return False
    return bool(re.match(r'^[\w-]+$', val))

@medicoes_bp.route('/api/salvar_dados', methods=['POST'])
def api_salvar_dados():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "JSON invÃ¡lido"}), 400

        # Gateway ID
        raw_gateway = data.get('gateway_id')
        if raw_gateway is not None:
            if not is_valid_gateway_id(raw_gateway):
                return jsonify({"success": False, "error": "gateway_id invÃ¡lido"}), 400
            gateway_id = raw_gateway.strip()
        else:
            gateway_id = DEFAULT_GATEWAY_ID

        # Sender Address
        sender = data.get('senderAddress')
        if type(sender) is bool or not isinstance(sender, int) or not (1 <= sender <= 65534):
            return jsonify({"success": False, "error": "senderAddress invÃ¡lido"}), 400

        # Temperaturas (ds1-ds6)
        for i in range(1, 7):
            t = data.get(f'temp_ds{i}')
            if t is not None:
                if type(t) is bool or not isinstance(t, (int, float)):
                    return jsonify({"success": False, "error": f"temp_ds{i} invÃ¡lido"}), 400

        # RSSI
        rssi = data.get('rssi')
        if rssi is not None:
            if type(rssi) is bool or not isinstance(rssi, (int, float)):
                return jsonify({"success": False, "error": "rssi invÃ¡lido"}), 400

        # Persistir
        if MedicaoModel.salvar(data, gateway_id):
            return jsonify({
                "success": True,
                "message": "MediÃ§Ã£o salva com sucesso",
                "sensor_id": sender,
                "gateway_id": gateway_id
            }), 201

    except Exception as e:
        return jsonify({"success": False, "error": "Erro interno no servidor"}), 500

@medicoes_bp.route('/api/medicoes/<int:sensor_id>', methods=['GET'])
def get_medicoes(sensor_id):
    try:
        limite = request.args.get('limite', default=100, type=int)
        gateway_id = request.args.get('gateway_id')
        dados = MedicaoModel.get_por_sensor(sensor_id, limite, gateway_id)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@medicoes_bp.route('/api/medicoes', methods=['GET'])
def get_medicoes_periodo():
    try:
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        sensor_id = request.args.get('sensor_id')
        gateway_id = request.args.get('gateway_id')

        if not inicio or not fim:
            return jsonify({"success": False, "error": "ParÃ¢metros 'inicio' e 'fim' sÃ£o obrigatÃ³rios."}), 400

        dados = MedicaoModel.get_por_periodo(inicio, fim, sensor_id, gateway_id)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@medicoes_bp.route('/api/medicoes/recentes', methods=['GET'])
def get_recentes():
    try:
        sensor_id = request.args.get('sensor_id')
        gateway_id = request.args.get('gateway_id')
        dados = MedicaoModel.get_recentes(sensor_id, gateway_id)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@medicoes_bp.route('/api/medicoes/estatisticas', methods=['GET'])
def get_estatisticas():
    try:
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        if bool(inicio) != bool(fim):
            return jsonify({"success": False, "error": "Informe 'inicio' e 'fim' juntos."}), 400

        dados = MedicaoModel.get_estatisticas_por_sensor(inicio, fim)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@medicoes_bp.route('/api/status', methods=['GET'])
def get_status():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT sensor_id, MAX(data_hora) as ultima_transmissao
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
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            if cursor: cursor.close()
            conn.close()
