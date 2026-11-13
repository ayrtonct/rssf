"""Point profiles and UTC status shared by all dashboard endpoints."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import config
from identity import NODE_GATEWAYS


def utc_datetime(value):
    if isinstance(value, (bytes, bytearray)):
        value = value.decode('utf-8')
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def iso_utc(value):
    return utc_datetime(value).isoformat().replace('+00:00', 'Z')


# Separate the storage convention from UTC API/server timestamps.
SAO_LUIS = ZoneInfo('America/Fortaleza')


def database_datetime(value):
    """Interpret naive MySQL DATETIME as Sao Luis, never as UTC."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode('utf-8')
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=SAO_LUIS)
    return value.astimezone(SAO_LUIS)


def database_iso_utc(value):
    return iso_utc(database_datetime(value))


def database_filter(value):
    """Offset-bearing API dates become naive local DATETIME SQL parameters.

    Naive API inputs retain the existing documented UTC interpretation.
    """
    return utc_datetime(value).astimezone(SAO_LUIS).replace(tzinfo=None)


def point_profile(sensor_id, gateway_id):
    # Accept the receiver's fallback gateway as well as the configured ID, while
    # preserving isolation if a different explicit gateway is sent for this sensor.
    sensor_key = str(sensor_id)
    laboratory = sensor_key in config.lab_sensor_ids() and (
        sensor_key not in NODE_GATEWAYS or gateway_id == config.LAB_GATEWAY_ID
    ) and gateway_id in (config.LAB_GATEWAY_ID, config.DEFAULT_GATEWAY_ID, 'gateway_legacy', None, '')
    return {
        'mode': 'laboratory' if laboratory else 'legacy',
        'has_sensors': not laboratory,
        'expected_interval_minutes': 480 if laboratory else 30,
        'online_minutes': config.LAB_ONLINE_MINUTES if laboratory else config.STATUS_ONLINE_MINUTES,
        'offline_minutes': config.LAB_OFFLINE_MINUTES if laboratory else config.STATUS_OFFLINE_MINUTES,
    }


def status_for(reading, now=None):
    now = utc_datetime(now or datetime.now(timezone.utc))
    profile = point_profile(reading['sensor_id'], reading['gateway_id'])
    last = utc_datetime(reading['data_hora'])
    minutes = (now - last).total_seconds() / 60
    # A future timestamp is a clock problem, not evidence of connectivity.
    if minutes < -1:
        status = 'unknown'
    elif minutes < profile['online_minutes']:
        status = 'online'
    elif minutes < profile['offline_minutes']:
        status = 'instavel'
    else:
        status = 'offline'
    return {
        'sensor_id': reading['sensor_id'], 'gateway_id': reading['gateway_id'],
        'ultima_transmissao': iso_utc(last), 'status': status,
        'minutos_desde_ultima': max(0, int(minutes)),
        'server_time': iso_utc(now), 'profile': profile,
    }
