#include <Arduino.h>
#include <LoRa_E32.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>

// pinagem
#define SAMPLE_TIME     1800000 // 30 min em ms
#define PIN_TX  17
#define PIN_RX  16
#define PIN_M0  19
#define PIN_M1  4
#define PIN_AUX 22
#define ONE_WIRE_BUS    15

// Endereço/canal do DESTINO (= receptor)
#define DEST_ADDH 0x00
#define DEST_ADDL 0x01
#define DEST_CHAN 0x04

// struct contendo dados a serem enviados
struct __attribute__((packed)) Packet {
  uint16_t senderAddress;
  float digTemperature[6];
};

// variáveis para definir endereço do nó sensor
uint16_t NODE_ADDRESS;
uint8_t mac[6];

// --- ENDEREÇOS DOS SENSORES (Confirmados por você) ---
DeviceAddress sensores[] = {
  { 0x28, 0x60, 0xE8, 0x2A, 0x1C, 0x19, 0x01, 0xA3 }, // S1
  { 0x28, 0xF0, 0xBE, 0x27, 0x1B, 0x19, 0x01, 0xFC }, // S2
  { 0x28, 0x98, 0x5E, 0x03, 0x1B, 0x19, 0x01, 0x3A }, // S3
  { 0x28, 0xEB, 0x87, 0xF5, 0x20, 0x19, 0x01, 0x31 }, // S4
  { 0x28, 0x33, 0x5B, 0x0F, 0x1C, 0x19, 0x01, 0x24 }, // S5
  { 0x28, 0x25, 0x58, 0x25, 0x1B, 0x19, 0x01, 0x92 }  // S6
};

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Inicialização corrigida com todos os parâmetros necessários
HardwareSerial loraSerial(2);
LoRa_E32 e32(&loraSerial, PIN_AUX, PIN_M0, PIN_M1);

void configureModule();
void printModuleConfig();

void setup() {
  Serial.begin(115200);

  // atribuição de endereço para o nó sensor via endereço MAC 
  WiFi.macAddress(mac);
  NODE_ADDRESS = ((uint16_t)mac[4] << 8) | mac[5];
  if (NODE_ADDRESS == 0xFFFF) NODE_ADDRESS = 0xFFFE; // proteção contra envio broadcast
  if (NODE_ADDRESS == 0x0000) NODE_ADDRESS = 0x0001; // proteção contra possíveis erros de leitura
 
  e32.begin();

  // configuração dos parâmetros do rádio
  e32.setMode(MODE_3_SLEEP);
  configureModule();
  delay(100);
  printModuleConfig();

  e32.setMode(MODE_0_NORMAL);
 
  sensors.begin();
  
  // Coleta de dados dos 6 sensores DS18B20
  sensors.requestTemperatures();
  struct Packet packet;
  packet.senderAddress = NODE_ADDRESS;
  
  for(int i = 0; i < 6; i++) {
    packet.digTemperature[i] = sensors.getTempC(sensores[i]);
  }

  // Envio do pacote via LoRa
  ResponseStatus rs = e32.sendFixedMessage(DEST_ADDH, DEST_ADDL, DEST_CHAN, &packet, sizeof(Packet));
  Serial.printf("Envio: %s\n", rs.getResponseDescription().c_str());
  
  // aguarda o AUX subir (transmissão concluída)
  while (digitalRead(PIN_AUX) == LOW) {
    delay(1);
  }
  delay(20); // margem de segurança após AUX subir 

  // Entra em Deep Sleep para economizar bateria
  Serial.println("Entrando em Deep Sleep...");
  e32.setMode(MODE_3_SLEEP);
  esp_sleep_enable_timer_wakeup((uint64_t)SAMPLE_TIME * 1000ULL);
  esp_deep_sleep_start();
}

void loop() {
  // O código não chega aqui devido ao Deep Sleep
}

void configureModule() {
    ResponseStructContainer rsc = e32.getConfiguration();
    if (rsc.status.code != SUCCESS) {
        Serial.printf("[FATAL] Modulo nao responde: %s\n", rsc.status.getResponseDescription());
        while(1) delay(1000);
    }
    Configuration* cfg = (Configuration*)rsc.data;
    cfg->ADDH = NODE_ADDRESS >> 8;
    cfg->ADDL = NODE_ADDRESS & 0xFF;
    cfg->CHAN = DEST_CHAN;
    cfg->SPED.uartBaudRate = UART_BPS_9600;
    cfg->SPED.airDataRate = AIR_DATA_RATE_010_24; // 2.4 kbps
    cfg->SPED.uartParity = MODE_00_8N1;
    cfg->OPTION.fixedTransmission = FT_FIXED_TRANSMISSION;
    cfg->OPTION.transmissionPower = POWER_20;          // 20 dBm
    cfg->OPTION.wirelessWakeupTime = WAKE_UP_250;
    cfg->OPTION.fec = FEC_1_ON;
    cfg->OPTION.ioDriveMode = IO_D_MODE_PUSH_PULLS_PULL_UPS;

    ResponseStatus rs = e32.setConfiguration(*cfg, WRITE_CFG_PWR_DWN_SAVE);
    Serial.printf("Gravando config: %s\n", rs.getResponseDescription().c_str());
    rsc.close();
}

void printModuleConfig() {
    ResponseStructContainer rsc = e32.getConfiguration();
    if (rsc.status.code == SUCCESS) {
        Configuration* cfg = (Configuration*)rsc.data;
        Serial.println(F("=== Configuracao do modulo E32 ==="));
        Serial.printf("  Canal   : %d\n", cfg->CHAN);
        Serial.printf("  Endereco: 0x%02X%02X\n", cfg->ADDH, cfg->ADDL);
        Serial.printf("  Baud    : %d\n", cfg->SPED.uartBaudRate);
        Serial.printf("  Air rate: %d\n", cfg->SPED.airDataRate);
        Serial.printf("  Potencia: %d\n", cfg->OPTION.transmissionPower);
        Serial.printf("  Fixed TX: %d\n", cfg->OPTION.fixedTransmission);
        rsc.close();
    }
}