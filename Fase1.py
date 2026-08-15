import config

query_1a = """
SELECT 
    c.relname AS tabla,
    c.reltuples::bigint AS filas_estimadas,
    c.relpages AS paginas_estimadas,
    pg_size_pretty(pg_total_relation_size(c.oid)) AS tamano_total
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'employees' AND c.relkind = 'r'
ORDER BY c.reltuples DESC;
"""
df_1a = config.run_query(query_1a)
df_1a

query_1b = """
SELECT 
    c.relname AS tabla,
    a.attname AS columna,
    t.typname AS tipo_dato
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid
JOIN pg_type t ON t.oid = a.atttypid
WHERE n.nspname = 'employees' 
  AND c.relkind = 'r' 
  AND a.attnum > 0 
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
"""
df_1b = config.run_query(query_1b)
df_1b

query_1c = """
SELECT 
    c.relname AS tabla,
    i.relname AS indice,
    ix.indisprimary AS es_llave_primaria,
    ix.indisunique AS es_unique,
    pg_get_indexdef(ix.indexrelid) AS definicion_columnas
FROM pg_index ix
JOIN pg_class c ON c.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'employees'
ORDER BY c.relname, i.relname;
"""
df_1c = config.run_query(query_1c)
df_1c