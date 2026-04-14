# models/medicao.py
import mysql.connector
from config import DB_CONFIG

class MedicaoModel:
    SENSOR_COLUMNS = ('ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'ds6')

    @staticmethod
    def salvar(data):
        # Ordem: id, s1, s2, s3, s4, s5, s6, rssi
        values = (
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
                     (sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(sql, values)
            conn.commit()
            return True
        except Exception as e:
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
            "sensor_id": row[2],
            "temp_ds1": row[3],
            "temp_ds2": row[4],
            "temp_ds3": row[5],
            "temp_ds4": row[6],
            "temp_ds5": row[7],
            "temp_ds6": row[8],
            "rssi": row[9]
        }

    @staticmethod
    def get_por_sensor(sensor_id, limite=100):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            sql = "SELECT id, created_at, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi FROM medicoes WHERE sensor_id = %s ORDER BY created_at DESC LIMIT %s"
            cursor.execute(sql, (sensor_id, int(limite)))
            rows = cursor.fetchall()
            return [MedicaoModel._to_dict(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor: cursor.close()
                conn.close()

    @staticmethod
    def get_por_periodo(inicio, fim):
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            sql = "SELECT id, created_at, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi FROM medicoes WHERE created_at BETWEEN %s AND %s ORDER BY created_at DESC"
            cursor.execute(sql, (inicio, fim))
            rows = cursor.fetchall()
            return [MedicaoModel._to_dict(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if conn and conn.is_connected():
                if cursor: cursor.close()
                conn.close()

    @staticmethod
    def get_recentes():
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            sql = """
                SELECT id, created_at, sensor_id, temp_ds1, temp_ds2, temp_ds3, temp_ds4, temp_ds5, temp_ds6, rssi 
                FROM medicoes m1
                WHERE created_at = (
                    SELECT MAX(created_at) 
                    FROM medicoes m2 
                    WHERE m1.sensor_id = m2.sensor_id
                )
            """
            cursor.execute(sql)
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
                sql += " WHERE created_at BETWEEN %s AND %s"
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
