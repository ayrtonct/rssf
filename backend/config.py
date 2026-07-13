import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GATEWAY_ID = os.getenv('DEFAULT_GATEWAY_ID', 'gateway_legacy')

DB_CONFIG = {
    'host':     os.getenv('MYSQLHOST'),
    'user':     os.getenv('MYSQLUSER'),
    'password': os.getenv('MYSQLPASSWORD'),
    'database': os.getenv('MYSQLDATABASE'),
    'port':     int(os.getenv('MYSQLPORT', 3306)),
    'use_pure': True
}

SERVER_HOST = '0.0.0.0'
SERVER_PORT = int(os.getenv('PORT', 5000))
