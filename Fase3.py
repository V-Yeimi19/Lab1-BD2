import config

config.run_query("""
CREATE TABLE IF NOT EXISTS employees.audit_salary_2025 (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    old_amount BIGINT,
    new_amount BIGINT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""")

config.run_query("""
CREATE OR REPLACE FUNCTION employees.fn_validar_salario()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount < 30000 THEN
        RAISE EXCEPTION 'El salario ($%) no puede ser inferior al mínimo legal ($30,000)', NEW.amount;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_salario ON employees.salary;
CREATE TRIGGER trg_validar_salario
BEFORE INSERT ON employees.salary
FOR EACH ROW
EXECUTE FUNCTION employees.fn_validar_salario();
""")

config.run_query("""
CREATE OR REPLACE PROCEDURE employees.sp_ajustar_salario(
    p_employee_id BIGINT,
    p_nuevo_monto BIGINT,
    p_anio INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_salario_actual BIGINT;
    v_tabla_audit TEXT;
BEGIN
    -- 1. Obtener salario vigente
    SELECT amount INTO v_salario_actual
    FROM employees.salary
    WHERE employee_id = p_employee_id AND to_date > CURRENT_DATE
    ORDER BY from_date DESC
    LIMIT 1;

    -- 2. Cerrar registro de salario vigente
    UPDATE employees.salary
    SET to_date = CURRENT_DATE
    WHERE employee_id = p_employee_id AND to_date > CURRENT_DATE;

    -- 3. Insertar nuevo salario (el trigger valida automáticamente)
    INSERT INTO employees.salary (employee_id, amount, from_date, to_date)
    VALUES (p_employee_id, p_nuevo_monto, CURRENT_DATE, '9999-01-01');

    -- 4. Inserción dinámica de auditoría por año
    v_tabla_audit := format('employees.audit_salary_%s', p_anio);
    EXECUTE format(
        'INSERT INTO %s (employee_id, old_amount, new_amount, changed_at) VALUES ($1, $2, $3, NOW())',
        v_tabla_audit
    ) USING p_employee_id, v_salario_actual, p_nuevo_monto;
END;
$$;
""")

# 1. Llamada válida
config.run_query("CALL employees.sp_ajustar_salario(10001, 75000, 2025);")

# 2. Llamada que debe fallar por Trigger (< 30000)
try:
    config.run_query("CALL employees.sp_ajustar_salario(10001, 20000, 2025);")
except Exception as e:
    print("Excepción capturada correctamente:", e)

# 3. Llamada que debe fallar por tabla inexistente (2099)
try:
    config.run_query("CALL employees.sp_ajustar_salario(10001, 75000, 2099);")
except Exception as e:
    print("Excepción capturada correctamente:", e)