LEGACY_GATEWAY_ID = 'gateway_legacy'

NODE_GATEWAYS = {
    '1': 'gateway_node_1',
    '44204': 'gateway_node_2',
}


def canonical_gateway_id(sensor_id, gateway_id):
    """Map only the known legacy node/gateway pair to its stable identity."""
    sensor_key = str(sensor_id) if sensor_id is not None else None
    if gateway_id in (None, '', LEGACY_GATEWAY_ID) and sensor_key in NODE_GATEWAYS:
        return NODE_GATEWAYS[sensor_key]
    return gateway_id


def gateway_query_values(sensor_id, gateway_id):
    """Include that node's old rows when its canonical gateway is requested."""
    if not gateway_id:
        return ()
    sensor_key = str(sensor_id) if sensor_id is not None else None
    if sensor_key in NODE_GATEWAYS and gateway_id == NODE_GATEWAYS[sensor_key]:
        return (gateway_id, LEGACY_GATEWAY_ID)
    return (gateway_id,)
