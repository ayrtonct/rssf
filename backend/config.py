import os
import re
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GATEWAY_ID = os.getenv('DEFAULT_GATEWAY_ID', 'gateway_unknown')

DB_CONFIG = {
    'host':     os.getenv('MYSQLHOST'),
    'user':     os.getenv('MYSQLUSER'),
    'password': os.getenv('MYSQLPASSWORD'),
    'database': os.getenv('MYSQLDATABASE'),
    'port':     int(os.getenv('MYSQLPORT', 3306)),
    'use_pure': True,
    # DATETIME stores Sao Luis wall time; CURRENT_TIMESTAMP must use the same zone.
    'time_zone': '-03:00',
    'connection_timeout': 5,
}

SERVER_HOST = '0.0.0.0'
SERVER_PORT = int(os.getenv('PORT', 5000))

# Preserve the deployed nodes' cadence. Lab thresholds are point-specific.
STATUS_ONLINE_MINUTES = int(os.getenv('STATUS_ONLINE_MINUTES', 60))
STATUS_OFFLINE_MINUTES = int(os.getenv('STATUS_OFFLINE_MINUTES', 180))
if not 0 < STATUS_ONLINE_MINUTES < STATUS_OFFLINE_MINUTES:
    raise ValueError('Status exige 0 < STATUS_ONLINE_MINUTES < STATUS_OFFLINE_MINUTES')

LAB_SENSOR_ID = os.getenv('LAB_SENSOR_ID', '').strip()
LAB_GATEWAY_ID = os.getenv('LAB_GATEWAY_ID', 'gateway_lab_01').strip()
LAB_ONLINE_MINUTES = int(os.getenv('LAB_ONLINE_MINUTES', 540))
LAB_OFFLINE_MINUTES = int(os.getenv('LAB_OFFLINE_MINUTES', 1440))


def parse_lab_sensor_ids(value):
    """LAB_SENSOR_ID aceita um ou mais senderAddress separados por virgula.

    Varios nos de laboratorio podem enviar pelo mesmo LAB_GATEWAY_ID (por
    exemplo, um no com buffer e outro sem, no teste comparativo). Cada par
    (sensor_id, gateway_id) continua sendo um ponto independente.
    """
    ids = []
    for part in (value or '').split(','):
        part = part.strip()
        if not part:
            continue
        if not part.isdecimal() or not 1 <= int(part) <= 65534:
            raise ValueError('LAB_SENSOR_ID deve conter IDs entre 1 e 65534, separados por virgula')
        ids.append(str(int(part)))
    return frozenset(ids)


def lab_sensor_ids():
    # Lido a cada chamada para que testes e recarga de configuracao vejam o valor atual.
    return parse_lab_sensor_ids(LAB_SENSOR_ID)


parse_lab_sensor_ids(LAB_SENSOR_ID)
if not 0 < LAB_ONLINE_MINUTES < LAB_OFFLINE_MINUTES:
    raise ValueError('Limites de status do laboratorio invalidos')
if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', LAB_GATEWAY_ID):
    raise ValueError('LAB_GATEWAY_ID invalido')
