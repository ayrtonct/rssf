#include <Arduino.h>
#include <LoRa_E220.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define TX_PIN 17
#define RX_PIN 16
#define AUX_PIN 5
#define M1_PIN 4
#define M0_PIN 2

struct Packet {
  uint16_t senderAddress;
  float digTemperature[6];
};

LoRa_E220 e220((byte)TX_PIN, (byte)RX_PIN, &Serial2, (byte)AUX_PIN, (byte)M0_PIN, (byte)M1_PIN, UART_BPS_RATE_9600, SERIAL_8N1);
const char* serverURL = "http://172.17.32.196:5000/api/salvar_dados";

void setup() {
  Serial.begin(115200);
  WiFi.begin("LSP/UEMA", "Asfaltosolos23");
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  if (!e220.begin()) {
    Serial.println("[RX] Falha ao iniciar E220.");
    return;
  }

  // Endereco dedicado ao transmissor de laboratorio; nao aceita broadcast.
  const byte receiverAddH = 0x00;
  const byte receiverAddL = 0x01;
  const byte labChannel = 0x0F;
  ResponseStructContainer c = e220.getConfiguration();
  if (c.status.code != E220_SUCCESS || c.data == nullptr) {
    Serial.println("[RX] Falha ao ler configuracao E220.");
    c.close();
    return;
  }
  Configuration configuration = *(Configuration*)c.data;
  c.close();
  if (configuration.CHAN != labChannel || configuration.ADDH != receiverAddH || configuration.ADDL != receiverAddL) {
    configuration.CHAN = labChannel;
    configuration.ADDH = receiverAddH;
    configuration.ADDL = receiverAddL;
    ResponseStatus status = e220.setConfiguration(configuration, WRITE_CFG_PWR_DWN_SAVE);
    Serial.printf("[RX] Configuracao de destino=%02X:%02X canal=%u: %s\\n",
                  receiverAddH, receiverAddL, labChannel, status.getResponseDescription().c_str());
    if (status.code != E220_SUCCESS) return;
  } else {
    Serial.printf("[RX] Endereco dedicado=%02X:%02X canal=%u\\n", receiverAddH, receiverAddL, labChannel);
  }

  // Receptor alimentado pela rede: escuta continua dispensa o duty-cycle do WOR
  e220.setMode(MODE_0_NORMAL);
}

void loop() {
  if (e220.available() > 0) {
    ResponseStructContainer rc = e220.receiveMessageRSSI(sizeof(Packet));
    if (rc.status.code == E220_SUCCESS) {
      Packet packet = *(Packet*)rc.data;
      float rssi = (120.0 / 255.0) * rc.rssi - 120.0;

      StaticJsonDocument<512> doc;
      doc["senderAddress"] = packet.senderAddress;
      doc["rssi"] = rssi;
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
    }
    rc.close();
  }
}
