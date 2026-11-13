"""Teste comparativo: varios nos de laboratorio no mesmo gateway."""
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import config
from app import app
from identity import canonical_gateway_id, gateway_query_values
from monitoring import point_profile
from test_batches import payload


def batch_from(sender, readings=16):
    data = payload()
    data['senderAddress'] = sender
    data['medicoes'] = data['medicoes'][-readings:]
    return data


class LabSensorIdParsingTests(unittest.TestCase):
    def test_accepts_single_list_and_whitespace(self):
        self.assertEqual(config.parse_lab_sensor_ids('21768'), {'21768'})
        self.assertEqual(config.parse_lab_sensor_ids(' 21768 , 4512,'), {'21768', '4512'})
        self.assertEqual(config.parse_lab_sensor_ids('021768'), {'21768'})

    def test_empty_disables(self):
        self.assertEqual(config.parse_lab_sensor_ids(''), frozenset())
        self.assertEqual(config.parse_lab_sensor_ids(' , '), frozenset())

    def test_rejects_invalid_ids(self):
        for value in ('0', '65535', 'abc', '21768;4512', '-5', '1.5'):
            with self.assertRaises(ValueError, msg=value):
                config.parse_lab_sensor_ids(value)


class MultipleLabNodesTests(unittest.TestCase):
    def setUp(self):
        lab = patch.multiple('config', LAB_SENSOR_ID='21768,4512', LAB_GATEWAY_ID='gateway_lab_01')
        lab.start()
        self.addCleanup(lab.stop)
        self.client = app.test_client()
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value
        self.cursor.fetchone.return_value = (datetime(2026, 11, 13, 10, 0),)
        connect = patch('models.medicao.mysql.connector.connect', return_value=self.connection)
        self.connect = connect.start()
        self.addCleanup(connect.stop)

    def test_buffered_and_unbuffered_nodes_both_save_as_separate_points(self):
        buffered = self.client.post('/api/salvar_dados', json=batch_from(21768, 16))
        self.assertEqual(buffered.status_code, 201)
        self.assertEqual(buffered.json['medicoes_salvas'], 16)
        buffered_rows = self.cursor.executemany.call_args.args[1]

        unbuffered = self.client.post('/api/salvar_dados', json=batch_from(4512, 1))
        self.assertEqual(unbuffered.status_code, 201)
        self.assertEqual(unbuffered.json['medicoes_salvas'], 1)
        unbuffered_rows = self.cursor.executemany.call_args.args[1]

        self.assertEqual({(row[1], row[2]) for row in buffered_rows}, {('gateway_lab_01', 21768)})
        self.assertEqual({(row[1], row[2]) for row in unbuffered_rows}, {('gateway_lab_01', 4512)})

    def test_unlisted_sender_on_lab_gateway_cannot_send_batches(self):
        response = self.client.post('/api/salvar_dados', json=batch_from(999, 1))
        self.assertEqual(response.status_code, 400)
        self.connect.assert_not_called()

    def test_both_nodes_get_laboratory_profile_and_installed_nodes_stay_legacy(self):
        for sender in (21768, 4512):
            self.assertEqual(point_profile(sender, 'gateway_lab_01')['mode'], 'laboratory')
            self.assertEqual(canonical_gateway_id(sender, 'gateway_unknown'), 'gateway_lab_01')
            self.assertIn('gateway_lab_01', gateway_query_values(sender, 'gateway_lab_01'))
        self.assertEqual(point_profile(1, 'gateway_node_1')['mode'], 'legacy')
        self.assertEqual(canonical_gateway_id(44204, None), 'gateway_node_2')

    def test_installed_node_id_listed_as_lab_keeps_its_own_gateway(self):
        with patch('config.LAB_SENSOR_ID', '21768,44204'):
            self.assertEqual(point_profile(44204, 'gateway_node_2')['mode'], 'legacy')
            self.assertEqual(canonical_gateway_id(44204, None), 'gateway_node_2')
            self.assertEqual(point_profile(44204, 'gateway_lab_01')['mode'], 'laboratory')


if __name__ == '__main__':
    unittest.main()
