#include <Arduino.h>
#include <LoRa_E220.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define SAMPLE_TIME     1800000 // 30 min em ms
#define TX_PIN          17
#define RX_PIN          16
#define AUX_PIN         5
#define M1_PIN          4
#define M0_PIN          2
#define ONE_WIRE_BUS    15

#define NODE_ADDRESS    0x0002
#define CHANNEL         0x0F

// --- ENDEREÇOS DOS SENSORES (Confirmados por você) ---
DeviceAddress sensores[] = {
  { 0x28, 0x60, 0xE8, 0x2A, 0x1C, 0x19, 0x01, 0xA3 }, // S1
  { 0x28, 0xF0, 0xBE, 0x27, 0x1B, 0x19, 0x01, 0xFC }, // S2
  { 0x28, 0x98, 0x5E, 0x03, 0x1B, 0x19, 0x01, 0x3A }, // S3
  { 0x28, 0xEB, 0x87, 0xF5, 0x20, 0x19, 0x01, 0x31 }, // S4
  { 0x28, 0x33, 0x5B, 0x0F, 0x1C, 0x19, 0x01, 0x24 }, // S5
  { 0x28, 0x25, 0x58, 0x25, 0x1B, 0x19, 0x01, 0x92 }  // S6
};

struct Packet {
  uint16_t senderAddress;
  float digTemperature[6];
};

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Inicialização corrigida com todos os parâmetros necessários
LoRa_E220 e220((byte)TX_PIN, (byte)RX_PIN, &Serial2, (byte)AUX_PIN, (byte)M0_PIN, (byte)M1_PIN, UART_BPS_RATE_9600, SERIAL_8N1);

void setup() {
  Serial.begin(115200);
  e220.begin();
  sensors.begin();

  // Configuração dos parâmetros do rádio
  ResponseStructContainer c = e220.getConfiguration();
  Configuration configuration = *(Configuration*)c.data;
  configuration.ADDL = (NODE_ADDRESS & 0xFF);
  configuration.ADDH = (NODE_ADDRESS >> 8);
  configuration.CHAN = CHANNEL;
  configuration.TRANSMISSION_MODE.fixedTransmission = FT_FIXED_TRANSMISSION;
  configuration.TRANSMISSION_MODE.enableRSSI = RSSI_ENABLED;
  e220.setConfiguration(configuration, WRITE_CFG_PWR_DWN_SAVE);
  c.close();

  e220.setMode(MODE_1_WOR_TRANSMITTER);
  
  // Coleta de dados dos 6 sensores DS18B20
  sensors.requestTemperatures();
  struct Packet packet;
  packet.senderAddress = NODE_ADDRESS;
  
  for(int i = 0; i < 6; i++) {
    packet.digTemperature[i] = sensors.getTempC(sensores[i]);
  }

  // Envio do pacote via LoRa
  ResponseStatus rs = e220.sendFixedMessage(BROADCAST_ADDRESS, BROADCAST_ADDRESS, CHANNEL, &packet, sizeof(Packet));
  Serial.println(rs.getResponseDescription());
  
  // Entra em Deep Sleep para economizar bateria
  Serial.println("Entrando em Deep Sleep...");
  e220.setMode(MODE_3_SLEEP);
  esp_sleep_enable_timer_wakeup((uint64_t)SAMPLE_TIME * 1000ULL);
  esp_deep_sleep_start();
}

void loop() {
  // O código não chega aqui devido ao Deep Sleep
}
