-- Migração: permitir todo o intervalo uint16_t usado pelos transmissores.
-- Execute uma única vez em bancos que já tenham a tabela medicoes.
ALTER TABLE medicoes
MODIFY COLUMN sensor_id SMALLINT UNSIGNED NOT NULL;
