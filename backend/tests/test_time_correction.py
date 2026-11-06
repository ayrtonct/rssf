from datetime import datetime
import pytest
from scripts.correct_local_times import correction


def test_correction_is_exact_and_retry_does_not_shift_again():
    entry = {'id': 4017, 'sensor_id': 8900, 'gateway_id': 'gateway_lab_01', 'data_hora': '2026-11-06 15:12:48'}
    current = {**entry, 'data_hora': datetime(2026, 11, 6, 15, 12, 48)}
    target = correction(entry, current)
    assert target == datetime(2026, 11, 6, 12, 12, 48)
    assert correction(entry, {**current, 'data_hora': target}) is None
    with pytest.raises(ValueError):
        correction(entry, {**current, 'gateway_id': 'gateway_node_2'})
    with pytest.raises(ValueError):
        correction(entry, {**current, 'data_hora': datetime(2026, 11, 6, 14)})
