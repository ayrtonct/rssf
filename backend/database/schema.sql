-- 1. Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS rssf;
USE rssf;

-- 2. Criação da Tabela de Medições
CREATE TABLE IF NOT EXISTS medicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Registro automático de data e hora
    sensor_id INT NOT NULL,                        -- ID do transmissor (0x0002)
    temp_ds1 FLOAT,                                -- Temperatura Sensor 1
    temp_ds2 FLOAT,                                -- Temperatura Sensor 2
    temp_ds3 FLOAT,                                -- Temperatura Sensor 3
    temp_ds4 FLOAT,                                -- Temperatura Sensor 4
    temp_ds5 FLOAT,                                -- Temperatura Sensor 5 
    temp_ds6 FLOAT,                                -- Temperatura Sensor 6 
    rssi FLOAT                                     -- Intensidade do sinal LoRa
);