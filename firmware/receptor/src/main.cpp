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
  
  e220.begin();
  e220.setMode(MODE_2_WOR_RECEIVER);
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
