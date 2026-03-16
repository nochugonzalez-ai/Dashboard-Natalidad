import os
import time
import psycopg2
from psycopg2 import sql
from google.cloud import bigquery

# --- Configuración de la Base de Datos (Variables de Entorno) ---
DB_HOST = os.environ.get("POSTGRES_HOST")
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")

def connect_to_db():
    """Intenta conectarse a PostgreSQL con reintentos."""
    conn = None
    retries = 10
    while retries > 0 and conn is None:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
        except psycopg2.OperationalError as e:
            print(f"Esperando a la DB... {e}. Reintentando en 5s...")
            retries -= 1
            time.sleep(5)
    return conn

def fetch_bigquery_data():
    """Obtiene los datos frescos de BigQuery."""
    try:
        client = bigquery.Client()
        sql_query = """
            SELECT
                CASE
                    WHEN day_of_week = 1 THEN '1. Domingo'
                    WHEN day_of_week = 2 THEN '2. Lunes'
                    WHEN day_of_week = 3 THEN '3. Martes'
                    WHEN day_of_week = 4 THEN '4. Miércoles'
                    WHEN day_of_week = 5 THEN '5. Jueves'
                    WHEN day_of_week = 6 THEN '6. Viernes'
                    WHEN day_of_week = 7 THEN '7. Sábado'
                END AS dia_de_la_semana,
                total_nacimientos
            FROM (
                SELECT
                    dia_num AS day_of_week,
                    SUM(nacimientos_totales) AS total_nacimientos
                FROM (
                    SELECT
                        EXTRACT(DAYOFWEEK FROM SAFE.DATE(year, month, day)) AS dia_num,
                        year,
                        SUM(plurality) AS nacimientos_totales
                    FROM
                        `bigquery-public-data.samples.natality`
                    WHERE
                        day IS NOT NULL AND month IS NOT NULL AND year > 0
                    GROUP BY
                        dia_num, year
                )
                WHERE dia_num IS NOT NULL 
                GROUP BY
                    day_of_week
            )
            ORDER BY
                day_of_week
        """
        query_job = client.query(sql_query)
        return list(query_job.result())
    except Exception as e:
        print(f"Error en BigQuery: {e}")
        return []

def insert_data(conn, data_rows):
    """Limpia la tabla e inserta los nuevos datos."""
    try:
        with conn.cursor() as cursor:
            print("Limpiando datos antiguos (Idempotencia)...")
            cursor.execute("CREATE TABLE IF NOT EXISTS natality_by_day (id SERIAL PRIMARY KEY, dia_de_la_semana VARCHAR(50), total_nacimientos BIGINT, collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            cursor.execute("TRUNCATE TABLE natality_by_day;")
            
            query = sql.SQL("INSERT INTO natality_by_day (dia_de_la_semana, total_nacimientos) VALUES (%s, %s)")
            rows_to_insert = [(row.dia_de_la_semana, row.total_nacimientos) for row in data_rows]
            cursor.executemany(query, rows_to_insert)
            conn.commit()
            print(f"¡{len(rows_to_insert)} filas actualizadas con éxito!")
    except Exception as e:
        print(f"Error al insertar: {e}")
        conn.rollback()

def run_pipeline():
    """Esta función agrupa todo el proceso."""
    print(f"\n--- Ejecución del Pipeline: {time.strftime('%H:%M:%S')} ---")
    rows = fetch_bigquery_data()
    if rows:
        conn = connect_to_db()
        if conn:
            insert_data(conn, rows)
            conn.close()
    else:
        print("No se obtuvieron datos en este ciclo.")

# --- BUCLE INFINITO ---
if __name__ == "__main__":
    # 3600 segundos = 1 hora
    INTERVALO = 3600 
    
    print(f"Servicio iniciado. Se ejecutará cada {INTERVALO/60} minutos.")
    
    while True:
        run_pipeline()
        print(f"Esperando a la próxima actualización...")
        time.sleep(INTERVALO)