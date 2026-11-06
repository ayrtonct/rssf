-- READ ONLY. Dates below locate candidates; they do NOT prove the writer's timezone.
SHOW CREATE TABLE medicoes;
SHOW TRIGGERS WHERE `Table` = 'medicoes';
SELECT @@global.time_zone AS fuso_global, @@session.time_zone AS fuso_sessao,
       @@system_time_zone AS fuso_sistema, NOW() AS horario_sessao,
       UTC_TIMESTAMP() AS horario_utc;
SELECT sensor_id, gateway_id, COUNT(*) AS total, MIN(id) AS primeiro_id,
       MAX(id) AS ultimo_id, MIN(data_hora) AS inicio, MAX(data_hora) AS fim
FROM medicoes GROUP BY sensor_id, gateway_id;
-- Confirm the reported empty interval around the change of writer.
SELECT id, sensor_id, gateway_id, data_hora FROM medicoes
WHERE data_hora BETWEEN '2026-10-20 16:00:00' AND '2026-10-20 22:00:00'
ORDER BY id;
-- Review these candidates against writer/deployment logs, including other writers.
-- Do NOT apply a global UPDATE using this date predicate.
SELECT id, sensor_id, gateway_id, data_hora,
       DATE_SUB(data_hora, INTERVAL 3 HOUR) AS horario_proposto_se_confirmado_utc
FROM medicoes WHERE data_hora >= '2026-10-20 19:00:00' ORDER BY id;
