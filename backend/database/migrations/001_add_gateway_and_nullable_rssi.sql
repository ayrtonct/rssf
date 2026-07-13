-- Migração: Adicionar suporte a gateway_id e permitir rssi NULL
-- Execute este script em bancos de dados existentes.

-- 1. Adicionar gateway_id
ALTER TABLE medicoes
ADD COLUMN gateway_id VARCHAR(64) DEFAULT 'gateway_legacy' AFTER data_hora;

-- Opcional: Se desejar que a coluna não seja nula para futuros inserts:
-- Primeiro garantimos que tudo tem um valor
UPDATE medicoes SET gateway_id = 'gateway_legacy' WHERE gateway_id IS NULL;
-- Depois definimos como NOT NULL
ALTER TABLE medicoes MODIFY COLUMN gateway_id VARCHAR(64) NOT NULL;

-- 2. Garantir que rssi aceita NULL
ALTER TABLE medicoes
MODIFY COLUMN rssi FLOAT NULL;

-- 3. Criar índice para otimizar os futuros filtros
CREATE INDEX idx_medicoes_sensor_gateway ON medicoes (sensor_id, gateway_id);
