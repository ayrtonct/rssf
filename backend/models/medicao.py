# models/medicao.py
import mysql.connector
from config import DB_CONFIG

class MedicaoModel:
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
