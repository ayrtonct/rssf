# models/medicao.py
import mysql.connector
from config import DB_CONFIG

class MedicaoModel:
    SENSOR_COLUMNS = ('ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'ds6')

    @staticmethod
    def salvar(data, gateway_id):
        # Ordem: gateway_id, id(sensor_id), s1, s2, s3, s4, s5, s6, rssi
        values = (
            gateway_id,
            data.get('senderAddress'),
            data.get('temp_ds1'), data.get('temp_ds2'),
            data.get('temp_ds3'), data.get('temp_ds4'),
            data.get('temp_ds5'), data.get('temp_ds6'),
            data.get('rssi')
        )

        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            sql = """INSERT INTO medicoes
                     (gateway_id, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, values)
            conn.commit()
            return True
        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()

    @staticmethod
    def _to_dict(row):
        val = row[1]
        if isinstance(val, (bytes, bytearray)):
            created_at_str = val.decode('utf-8')
        elif hasattr(val, 'isoformat'):
            created_at_str = val.isoformat()
        else:
            created_at_str = str(val)

        return {
            "id": row[0],
            "data_hora": created_at_str,
            "gateway_id": row[2],
            "sensor_id": row[3],
            "temp_ds1": row[4],
            "temp_ds2": row[5],
            "temp_ds3": row[6],
            "temp_ds4": row[7],
            "temp_ds5": row[8],
            "temp_ds6": row[9],
            "rssi": row[10]
        }

    @staticmethod
    def get_por_sensor(sensor_id, limite=100, gateway_id=None):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            sql = "SELECT id, data_hora, gateway_id, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi FROM medicoes WHERE sensor_id = %s"
            params = [sensor_id]

            if gateway_id:
                sql += " AND gateway_id = %s"
                params.append(gateway_id)

            sql += " ORDER BY data_hora DESC LIMIT %s"
            params.append(int(limite))

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [MedicaoModel._to_dict(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor: cursor.close()
                conn.close()

    @staticmethod
    def get_por_periodo(inicio, fim, sensor_id=None, gateway_id=None):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            sql = "SELECT id, data_hora, gateway_id, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi FROM medicoes WHERE data_hora BETWEEN %s AND %s"
            params = [inicio, fim]

            if sensor_id:
                sql += " AND sensor_id = %s"
                params.append(sensor_id)
            if gateway_id:
                sql += " AND gateway_id = %s"
                params.append(gateway_id)

            sql += " ORDER BY data_hora DESC"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [MedicaoModel._to_dict(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor: cursor.close()
                conn.close()

    @staticmethod
    def get_recentes(sensor_id=None, gateway_id=None):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            sql = """
                SELECT id, data_hora, gateway_id, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi
                FROM medicoes m1
                WHERE data_hora = (
                    SELECT MAX(data_hora)
                    FROM medicoes m2
                    WHERE m1.sensor_id = m2.sensor_id
            """
            params = []
            if sensor_id:
                sql += " AND m2.sensor_id = %s"
                params.append(sensor_id)
            if gateway_id:
                sql += " AND m2.gateway_id = %s"
                params.append(gateway_id)

            sql += ")"

            if sensor_id:
                sql += " AND m1.sensor_id = %s"
                params.append(sensor_id)
            if gateway_id:
                sql += " AND m1.gateway_id = %s"
                params.append(gateway_id)

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [MedicaoModel._to_dict(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor: cursor.close()
                conn.close()

    @staticmethod
    def get_estatisticas_por_sensor(inicio=None, fim=None):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            def valid_temp_expr(sensor):
                column = f"temp_{sensor}"
                return f"CASE WHEN {column} IS NOT NULL AND {column} <> -127 THEN {column} END"

            aggregate_sql = ", ".join(
                [
                    f"AVG({valid_temp_expr(sensor)}) AS avg_{sensor}, "
                    f"MAX({valid_temp_expr(sensor)}) AS max_{sensor}, "
                    f"MIN({valid_temp_expr(sensor)}) AS min_{sensor}, "
                    f"COUNT({valid_temp_expr(sensor)}) AS count_{sensor}"
                    for sensor in MedicaoModel.SENSOR_COLUMNS
                ]
            )

            sql = f"SELECT {aggregate_sql} FROM medicoes"
            params = []

            if inicio and fim:
                sql += " WHERE data_hora BETWEEN %s AND %s"
                params.extend([inicio, fim])

            cursor.execute(sql, tuple(params))
            row = cursor.fetchone() or {}

            return [
                {
                    "sensor_id": sensor,
                    "avg": row.get(f"avg_{sensor}"),
                    "max": row.get(f"max_{sensor}"),
                    "min": row.get(f"min_{sensor}"),
                    "count": row.get(f"count_{sensor}", 0)
                }
                for sensor in MedicaoModel.SENSOR_COLUMNS
            ]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()
