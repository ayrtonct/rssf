#include <Arduino.h>
#include <LoRa_E32.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define PIN_TX 17
#define PIN_RX 16
#define PIN_AUX 5
#define PIN_M0 4
#define PIN_M1 2

// Endereço do receptor
#define DEST_ADDH 0x00
#define DEST_ADDL 0x01
#define DEST_CHAN 0x04

struct __attribute__((packed)) Packet {
  uint16_t senderAddress;
  float digTemperature[6];
};

HardwareSerial loraSerial(2);
LoRa_E32 e32(&loraSerial, PIN_AUX, PIN_M0, PIN_M1);
const char* serverURL = "http://172.17.32.196:5000/api/salvar_dados";

void configureModule();
void printModuleConfig();

void setup() {
  Serial.begin(115200);
  WiFi.begin("LSP/UEMA", "Asfaltosolos23");
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  e32.begin();
  e32.setMode(MODE_3_SLEEP);

  // configuração dos parâmetros do rádio
  configureModule();
  delay(100);
  printModuleConfig();

  e32.setMode(MODE_0_NORMAL);
}

void loop() {
  if (e32.available() > 0) {
    delay(40);
    ResponseStructContainer rsc = e32.receiveMessage(sizeof(Packet));
    if (rsc.status.code == SUCCESS) {
      Packet packet = *(Packet*)rsc.data;

      StaticJsonDocument<512> doc;
      doc["senderAddress"] = packet.senderAddress;
      for(int i = 0; i < 6; i++) {
        String key = "temp_ds" + String(i+1);
        doc[key] = packet.digTemperature[i];
      }

      HTTPClient http;
      http.begin(serverURL);
      http.addHeader("Content-Type", "application/json");
      
      String json;
      serializeJson(doc, json);
      int httpCode = http.POST(json);
      
      Serial.printf("Enviado: %s | Status: %d\n", json.c_str(), httpCode);
      http.end();

      rsc.close();
    }
  }
}

void configureModule() {
    ResponseStructContainer rsc = e32.getConfiguration();
    if (rsc.status.code != SUCCESS) {
        Serial.printf("[FATAL] Modulo nao responde: %s\n", rsc.status.getResponseDescription());
        while(1) delay(1000);
    }
    Configuration* cfg = (Configuration*)rsc.data;

    cfg->ADDH = DEST_ADDH;
    cfg->ADDL = DEST_ADDL;
    cfg->CHAN = DEST_CHAN;
    cfg->SPED.uartBaudRate = UART_BPS_9600;
    cfg->SPED.airDataRate = AIR_DATA_RATE_010_24;
    cfg->SPED.uartParity = MODE_00_8N1;
    cfg->OPTION.fixedTransmission = FT_FIXED_TRANSMISSION;
    cfg->OPTION.transmissionPower = POWER_20;
    cfg->OPTION.wirelessWakeupTime = WAKE_UP_250;
    cfg->OPTION.fec = FEC_1_ON;
    cfg->OPTION.ioDriveMode = IO_D_MODE_PUSH_PULLS_PULL_UPS;

    ResponseStatus rs = e32.setConfiguration(*cfg, WRITE_CFG_PWR_DWN_SAVE);
    Serial.printf("Gravando config: %s\n", rs.getResponseDescription());
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
        Serial.printf("  Fixed TX: %d\n", cfg->OPTION.fixedTransmission);
        rsc.close();
    }
}