import threading
import time
import random
import config
import pandas as pd
from psycopg2 import errors


def ajustar_salario(employee_id: int, nuevo_salario: int, thread_id: int):
    """
    Llama al procedimiento sp_ajustar_salario desde un hilo.
    Obtiene una conexion del pool, ejecuta el procedimiento y
    confirma o revierte segun el resultado.
    """
    conn = None
    try:
        # Obtener conexion del pool
        conn = config.connection_pool.getconn()
        # Manejo manual de transaccion (no autocommit)
        conn.autocommit = False
        with conn.cursor() as cur:
            print(f"[Hilo {thread_id}] Intentando ajustar salario "
                  f"empleado={employee_id} monto=${nuevo_salario}")
            cur.execute(
                "CALL employees.sp_ajustar_salario(%s, %s, %s)",
                (employee_id, nuevo_salario, 2025)
            )
            conn.commit()
        print(f"[Hilo {thread_id}] Exito: empleado={employee_id} -> ${nuevo_salario}")

    except errors.CheckViolation as e:
        # Error especifico del trigger de salario minimo
        if conn:
            conn.rollback()
        print(f"[Hilo {thread_id}] Trigger rechazo el salario ${nuevo_salario}: {e.pgerror}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[Hilo {thread_id}] Error: {str(e)[:150]}")
    finally:
        if conn:
            # Siempre devolver la conexion al pool
            config.connection_pool.putconn(conn)


EMPLEADOS_PRUEBA = [10001, 10002, 10003, 10004, 10005]


def simular_ajustes_concurrentes(n_hilos=6):
    """
    Lanza n_hilos hilos que intentan ajustar salarios simultaneamente.
    Alterna entre salarios validos e invalidos para probar el trigger.
    """
    print(f"\n{'='*60}")
    print(f"Iniciando simulacion con {n_hilos} hilos concurrentes")
    print(f"{'='*60}")
    hilos = []
    for i in range(n_hilos):
        empleado = random.choice(EMPLEADOS_PRUEBA)
        # Alterna valido/invalido para ejercitar el trigger
        nuevo_salario = 75000 if i % 2 == 0 else 15000
        hilo = threading.Thread(
            target=ajustar_salario,
            args=(empleado, nuevo_salario, i + 1)
        )
        hilos.append(hilo)
        hilo.start()
        time.sleep(0.1)
    # Esperar a que todos los hilos terminen
    for hilo in hilos:
        hilo.join()
    print(f"{'='*60}")
    print("Simulacion completada\n")


def ver_auditoria():
    conn = config.connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT employee_id, old_amount, new_amount, changed_at
            FROM employees.audit_salary_2025
            ORDER BY changed_at DESC
            LIMIT 20;
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            print(f"\n{'='*60}")
            print("TABLA DE AUDITORIA - audit_salary_2025 (ultimos 20)")
            print(f"{'='*60}")
            print(df.to_string(index=False))
    finally:
        config.connection_pool.putconn(conn)


if __name__ == "__main__":
    try:
        # Verificar conexion inicial
        conn_test = config.connection_pool.getconn()
        print("Conexion a PostgreSQL exitosa")
        config.connection_pool.putconn(conn_test)
        # Lanzar simulacion concurrente
        simular_ajustes_concurrentes(n_hilos=6)
        # Ver resultados en auditoria
        ver_auditoria()
        config.connection_pool.closeall()
        print("\nPool de conexiones cerrado correctamente")
    except Exception as e:
        print(f"Error al conectar a PostgreSQL: {e}")
