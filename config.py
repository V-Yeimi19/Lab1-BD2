import psycopg2 
from psycopg2 import pool, sql, errors
import pandas as pd

# Configuren con sus credenciales
DB_CONFIG = {
 "host": "localhost",
 "port": 5434,
 "dbname": "Lab1-BD2",
 "user": "Lab1-BD2",
 "password": "Lab1-BD2"
}

def run_query(query, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                cols = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return pd.DataFrame(data, columns=cols)
            conn.commit()
    finally:
        conn.close()

# Prueba de conexión rápida
run_query("SELECT current_user, current_database(), version();")

# Pool con mínimo 2 y máximo 10 conexiones
connection_pool = pool.ThreadedConnectionPool(
 minconn=2,
 maxconn=10,
 **DB_CONFIG
)   

conn = connection_pool.getconn()