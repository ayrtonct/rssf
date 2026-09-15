import math
import re
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from config import DEFAULT_GATEWAY_ID
from identity import canonical_gateway_id
from models.medicao import MedicaoModel

medicoes_bp = Blueprint('medicoes', __name__)


def is_valid_gateway_id(value):
    if not value or not isinstance(value, str):
        return False
    value = value.strip()
    return 0 < len(value) <= 64 and bool(re.match(r'^[\w-]+$', value))


def is_valid_number(value):
    return type(value) is not bool and isinstance(value, (int, float)) and math.isfinite(value)


@medicoes_bp.route('/api/salvar_dados', methods=['POST'])
def api_salvar_dados():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not data:
            return jsonify({'success': False, 'error': 'JSON inválido'}), 400

        sender = data.get('senderAddress')
        if type(sender) is bool or not isinstance(sender, int) or not (1 <= sender <= 65534):
            return jsonify({'success': False, 'error': 'senderAddress inválido'}), 400

        raw_gateway = data.get('gateway_id')
        if raw_gateway is not None and not is_valid_gateway_id(raw_gateway):
            return jsonify({'success': False, 'error': 'gateway_id inválido'}), 400
        gateway_id = canonical_gateway_id(sender, raw_gateway.strip() if raw_gateway else None)
        gateway_id = gateway_id or DEFAULT_GATEWAY_ID

        for index in range(1, 7):
            temperature = data.get(f'temp_ds{index}')
            if temperature is not None and not is_valid_number(temperature):
                return jsonify({'success': False, 'error': f'temp_ds{index} inválido'}), 400

        rssi = data.get('rssi')
        if rssi is not None and not is_valid_number(rssi):
            return jsonify({'success': False, 'error': 'rssi inválido'}), 400

        if MedicaoModel.salvar(data, gateway_id):
            return jsonify({
                'success': True,
                'message': 'Medição salva com sucesso',
                'sensor_id': sender,
                'gateway_id': gateway_id,
            }), 201
    except Exception:
        return jsonify({'success': False, 'error': 'Erro interno no servidor'}), 500


@medicoes_bp.route('/api/medicoes/<int:sensor_id>', methods=['GET'])
def get_medicoes(sensor_id):
    try:
        limite = request.args.get('limite', default=100, type=int)
        gateway_id = request.args.get('gateway_id')
        return jsonify(MedicaoModel.get_por_sensor(sensor_id, limite, gateway_id)), 200
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500

@medicoes_bp.route('/api/medicoes', methods=['GET'])
def get_medicoes_periodo():
    try:
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        sensor_id = request.args.get('sensor_id')
        gateway_id = request.args.get('gateway_id')
        if not inicio or not fim:
            return jsonify({'success': False, 'error': "Parâmetros 'inicio' e 'fim' são obrigatórios."}), 400
        return jsonify(MedicaoModel.get_por_periodo(inicio, fim, sensor_id, gateway_id)), 200
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500


@medicoes_bp.route('/api/medicoes/recentes', methods=['GET'])
def get_recentes():
    try:
        sensor_id = request.args.get('sensor_id')
        gateway_id = request.args.get('gateway_id')
        return jsonify(MedicaoModel.get_recentes(sensor_id, gateway_id)), 200
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500


@medicoes_bp.route('/api/medicoes/estatisticas', methods=['GET'])
def get_estatisticas():
    try:
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        sensor_id = request.args.get('sensor_id')
        gateway_id = request.args.get('gateway_id')
        if bool(inicio) != bool(fim):
            return jsonify({'success': False, 'error': "Informe 'inicio' e 'fim' juntos."}), 400
        return jsonify(MedicaoModel.get_estatisticas_por_sensor(
            inicio, fim, sensor_id, gateway_id,
        )), 200
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500


@medicoes_bp.route('/api/status', methods=['GET'])
def get_status():
    try:
        agora = datetime.now()
        resultado = []
        for reading in MedicaoModel.get_recentes():
            ultima = reading['data_hora']
            if isinstance(ultima, (bytes, bytearray)):
                ultima = ultima.decode('utf-8')
            if isinstance(ultima, str):
                ultima = datetime.fromisoformat(ultima)

            delta = agora - ultima
            minutos = int(delta.total_seconds() / 60)
            if delta < timedelta(hours=1):
                status = 'online'
            elif delta < timedelta(hours=3):
                status = 'instavel'
            else:
                status = 'offline'

            resultado.append({
                'sensor_id': reading['sensor_id'],
                'gateway_id': reading['gateway_id'],
                'ultima_transmissao': ultima.strftime('%Y-%m-%d %H:%M:%S'),
                'status': status,
                'minutos_desde_ultima': minutos,
            })
        return jsonify(resultado), 200
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500
