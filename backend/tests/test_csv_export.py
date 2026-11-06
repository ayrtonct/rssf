import csv
import io
from datetime import datetime
from unittest.mock import MagicMock, patch

from app import app


def test_csv_streams_all_raw_readings_and_closes_connection():
    rows = [(i, datetime(2026, 4, 10, 12, 0), 85, -127, 30.125, None, 32, 33, -44)
            for i in range(1, 1202)]
    cursor = MagicMock()
    cursor.__iter__.return_value = iter(rows)
    connection = MagicMock()
    connection.cursor.return_value = cursor
    with patch('routes.medicoes.mysql.connector.connect', return_value=connection):
        response = app.test_client().get('/api/medicoes/csv?sensor_id=1&gateway_id=gateway_node_1')
        parsed = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip('\ufeff')), delimiter=';'))
    assert response.status_code == 200
    assert len(parsed) == 1202
    assert parsed[1][0] == '1' and parsed[-1][0] == '1201'
    assert parsed[1][2:6] == ['85', '-127', '30.125', '']
    assert 'America/Fortaleza' in parsed[0][1]
    assert parsed[1][1] == '2026-04-10 12:00:00-03:00'
    sql, params = cursor.execute.call_args.args
    assert 'LIMIT' not in sql.upper()
    assert params == (1, 'gateway_node_1', 'gateway_legacy')
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_csv_rejects_missing_point_and_invalid_dates():
    client = app.test_client()
    assert client.get('/api/medicoes/csv').status_code == 400
    assert client.get('/api/medicoes/csv?sensor_id=1&gateway_id=gateway_node_1&inicio=invalid&fim=invalid').status_code == 400
