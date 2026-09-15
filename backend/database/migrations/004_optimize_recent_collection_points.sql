-- Otimiza a descoberta da leitura mais recente por gateway e sensor.
-- Alteração apenas de desempenho: o backend funciona sem este índice.
-- A criação é condicionada porque o schema novo já contém o mesmo índice.

SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'medicoes'
      AND index_name = 'idx_medicoes_latest_point'
);

SET @create_index_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_medicoes_latest_point ON medicoes (sensor_id, gateway_id, data_hora, id)',
    'SELECT ''idx_medicoes_latest_point já existe'' AS info'
);

PREPARE create_index_statement FROM @create_index_sql;
EXECUTE create_index_statement;
DEALLOCATE PREPARE create_index_statement;
