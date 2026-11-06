from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app import app
from config import DB_CONFIG
from models.medicao import MedicaoModel
from monitoring import database_datetime, database_filter, database_iso_utc, status_for
from test_batches import payload


def test_database_wall_time_round_trip_preserves_old_node_two():
    local = datetime(2026, 8, 21, 16, 22, 43)
    row = (1804, local, 'gateway_legacy', 44204, 41.625, 41, 41, 42, 40, 40, -47)
    result = MedicaoModel._to_dict(row)
    assert result['data_hora'] == '2026-08-21T19:22:43Z'
    assert database_datetime(result['data_hora']).replace(tzinfo=None) == local
    assert result['temp_ds1'] == 41.625
    assert result['gateway_id'] == 'gateway_node_2'
    assert DB_CONFIG['time_zone'] == '-03:00'


def test_offsets_are_not_applied_twice_and_filters_cross_midnight():
    assert database_iso_utc('2026-11-06T15:00:00-03:00') == '2026-11-06T18:00:00Z'
    assert database_iso_utc('2026-11-06T18:00:00Z') == '2026-11-06T18:00:00Z'
    assert database_filter('2026-11-06T01:30:00Z') == datetime(2026, 11, 5, 22, 30)


def test_csv_filters_use_database_local_time():
    with patch('routes.medicoes.mysql.connector.connect') as connect:
        connect.return_value.cursor.return_value.__iter__.return_value = iter([])
        response = app.test_client().get('/api/medicoes/csv', query_string={
            'sensor_id': 44204, 'gateway_id': 'gateway_node_2',
            'inicio': '2026-08-21T19:00:00Z', 'fim': '2026-08-21T20:00:00Z',
        })
        response.get_data()
        assert response.status_code == 200
        params = connect.return_value.cursor.return_value.execute.call_args.args[1]
        assert params == (44204, 'gateway_node_2', 'gateway_legacy',
                          datetime(2026, 8, 21, 16), datetime(2026, 8, 21, 17))


def test_field_and_lab_share_local_clock_but_only_lab_reconstructs():
    received = datetime(2026, 11, 6, 1, 15)
    now = datetime(2026, 11, 6, 4, 15, tzinfo=timezone.utc)
    with patch.multiple('config', LAB_SENSOR_ID='8900', LAB_GATEWAY_ID='gateway_lab_01'), \
            patch('models.medicao.mysql.connector.connect') as connect:
        cursor = connect.return_value.cursor.return_value
        cursor.fetchone.return_value = (received,)
        client = app.test_client()
        for sensor_id in (1, 44204):
            assert client.post('/api/salvar_dados', json={'senderAddress': sensor_id, 'temp_ds1': 30}).status_code == 201
            cursor.executemany.assert_not_called()
            assert 'data_hora' not in cursor.execute.call_args.args[0]
        data = payload()
        data['senderAddress'] = 8900
        assert client.post('/api/salvar_dados', json=data).status_code == 201
        rows = cursor.executemany.call_args.args[1]
        assert len(rows) == 16
        assert rows[0][0] == received - timedelta(minutes=450)
        assert rows[-1][0] == received
        assert all(rows[i+1][0] - rows[i][0] == timedelta(minutes=30) for i in range(15))
        latest = MedicaoModel._to_dict((1, received, 'gateway_lab_01', 8900, *([None]*6), -49))
        assert status_for(latest, now)['minutos_desde_ultima'] == 0
        assert status_for(latest, now + timedelta(hours=8))['status'] == 'online'


def test_batches_require_explicit_lab_gateway_not_legacy_fallback():
    with patch.multiple('config', LAB_SENSOR_ID='8900', LAB_GATEWAY_ID='gateway_lab_01'), \
            patch('models.medicao.mysql.connector.connect') as connect:
        for gateway in (None, 'gateway_unknown', 'gateway_legacy', 'gateway_node_1', 'gateway_node_2'):
            data = payload()
            data['senderAddress'] = 8900
            if gateway is None:
                data.pop('gateway_id')
            else:
                data['gateway_id'] = gateway
            assert app.test_client().post('/api/salvar_dados', json=data).status_code == 400
        connect.assert_not_called()
