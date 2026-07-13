-- 1. Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS rssf;
USE rssf;

-- 2. Criação da Tabela de Medições
CREATE TABLE IF NOT EXISTS medicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Registro automático de data e hora
    gateway_id VARCHAR(64) NOT NULL,               -- Identificador do gateway
    sensor_id SMALLINT UNSIGNED NOT NULL,          -- ID uint16_t do transmissor
    temp_ds1 FLOAT,                                -- Temperatura Sensor 1
    temp_ds2 FLOAT,                                -- Temperatura Sensor 2
    temp_ds3 FLOAT,                                -- Temperatura Sensor 3
    temp_ds4 FLOAT,                                -- Temperatura Sensor 4
    temp_ds5 FLOAT,                                -- Temperatura Sensor 5 
    temp_ds6 FLOAT,                                -- Temperatura Sensor 6 
    rssi FLOAT NULL                                -- Intensidade do sinal LoRa
);

-- 3. Criação de Índices
CREATE INDEX idx_medicoes_sensor_gateway ON medicoes (sensor_id, gateway_id);
