#include <Arduino.h>

#include <stddef.h>
#include <LoRa_E220.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Pinagem conforme o commit do Kalebe: ESP32 TX GPIO17 -> E220 RXD;
// E220 TXD -> ESP32 RX GPIO16. Primeiro argumento da biblioteca = TX, segundo = RX.
#define ESP32_TX_PIN 16
#define ESP32_RX_PIN 17
#define AUX_PIN 22
#define M0_PIN 19
#define M1_PIN 4

#define BUFFER_SIZE 16

// Deve ser identico a LAB_GATEWAY_ID no backend.
const char* LAB_GATEWAY_ID = "gateway_lab_01";

// Endereco E220 dedicado; precisa coincidir com o destino do transmissor.
#define LAB_RECEIVER_ADDH 0xA7
#define LAB_RECEIVER_ADDL 0x68

// Precisa bater com o CHANNEL do transmissor: ele retuna pra esse canal so
// durante o envio (sendFixedMessage), entao o receptor tem que estar
// escutando nele - nao basta usar a config default/residual do modulo.
#define CHANNEL 0x0F

// Intervalo entre medicoes no transmissor (SAMPLE_TIME = 30 min)
#define INTERVALO_MIN 30

// estrutura dos subpacotes
struct __attribute__((__packed__)) SubPacket{
  int16_t digTemperature[6];
};

// estrutura do pacote principal. No ar vai so o cabecalho e as qntd_medicoes
// preenchidas: 15 B no no sem buffer, ate 195 B no no com buffer.
struct __attribute__((__packed__)) Packet {
  uint16_t senderAddress;
  uint8_t qntd_medicoes;
  SubPacket subpacket[BUFFER_SIZE];
};

LoRa_E220 e220((byte)ESP32_TX_PIN, (byte)ESP32_RX_PIN,
                 &Serial2, (byte)AUX_PIN, (byte)M0_PIN, (byte)M1_PIN,
                 UART_BPS_RATE_9600, SERIAL_8N1);
const char* serverURL = "https://rssf-production.up.railway.app/api/salvar_dados";

// Um comando de configuracao logo apos a resposta do anterior e rejeitado
// pelo E220 (FF FF FF): espera o AUX subir e mais 50 ms.
void esperaE220Livre() {
  unsigned long inicio = millis();
  while (digitalRead(AUX_PIN) == LOW && millis() - inicio < 1000) delay(5);
  delay(50);
}

// Le exatamente n bytes da UART do E220 (timeout padrao de 1 s do Serial2).
bool leExato(void* destino, size_t n) {
  return Serial2.readBytes((uint8_t*)destino, n) == n;
}

// Descarta o que sobrou de um pacote invalido para nao desalinhar o proximo.
void descartaUART() {
  delay(20);
  while (Serial2.available() > 0) Serial2.read();
}

void setup() {
  Serial.begin(115200);
  Serial.println("[DEBUG] setup() iniciou");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin("iPhone de Ayrton ", "12345678");
  Serial.printf("[WiFi] tentativa iniciada; status=%d. Inicializando E220 sem aguardar rede.\n", WiFi.status());

  bool beginOk = e220.begin();
  Serial.printf("[DEBUG] e220.begin() = %s\n", beginOk ? "OK" : "FALHOU");

  // Grava o canal no modulo em vez de confiar no que ja estava salvo nele
  esperaE220Livre();
  ResponseStructContainer c = e220.getConfiguration();
  Serial.printf("[DEBUG] getConfiguration() status = %s\n", c.status.getResponseDescription().c_str());
  if (c.status.code != E220_SUCCESS || c.data == nullptr) {
    Serial.println("[ERROR] E220 nao respondeu a leitura de configuracao; verifique UART, AUX, M0/M1 e alimentacao.");
    c.close();
    return;
  }
  Configuration configuration = *(Configuration*)c.data;
  Serial.printf("[DEBUG] canal atual = %d (esperado %d) | ADDH=%d ADDL=%d (esperado %d/%d, unicast) | RSSI=%d | AirDataRate=%s\n",
                configuration.CHAN, CHANNEL, configuration.ADDH, configuration.ADDL, LAB_RECEIVER_ADDH, LAB_RECEIVER_ADDL,
                configuration.TRANSMISSION_MODE.enableRSSI,
                configuration.SPED.getAirDataRateDescription().c_str());
  // O transmissor usa sendFixedMessage para o endereco dedicado abaixo; o E220
  // filtra pacotes destinados a outros receptores. O byte de RSSI apos cada
  // pacote so existe com enableRSSI ligado no modulo RECEPTOR.
  if (configuration.CHAN != CHANNEL || configuration.ADDH != LAB_RECEIVER_ADDH || configuration.ADDL != LAB_RECEIVER_ADDL
      || configuration.TRANSMISSION_MODE.enableRSSI != RSSI_ENABLED) {
    configuration.CHAN = CHANNEL;
    configuration.ADDH = LAB_RECEIVER_ADDH;
    configuration.ADDL = LAB_RECEIVER_ADDL;
    configuration.TRANSMISSION_MODE.enableRSSI = RSSI_ENABLED;
    esperaE220Livre();
    ResponseStatus rs = e220.setConfiguration(configuration, WRITE_CFG_PWR_DWN_SAVE);
    Serial.printf("[DEBUG] setConfiguration() status = %s\n", rs.getResponseDescription().c_str());
    if (rs.code != E220_SUCCESS) {
      Serial.println("[ERROR] E220 rejeitou a configuracao de endereco/canal/RSSI; receptor nao iniciou.");
      c.close();
      return;
    }
  } else {
    Serial.println("[DEBUG] canal, endereco e RSSI ja estavam corretos, nao precisou regravar");
  }
  c.close();

  // Receptor alimentado pela rede: escuta continua dispensa o duty-cycle do WOR
  esperaE220Livre();
  e220.setMode(MODE_0_NORMAL);
  Serial.println("[DEBUG] setup() concluido, modo NORMAL ativado, aguardando pacotes...");
}

void loop() {
  if (e220.available() <= 0) return;

  // Pacote de tamanho variavel: cabecalho, qntd_medicoes subpacotes e o byte
  // de RSSI. Le o cabecalho primeiro para saber quantos bytes vem depois.
  Packet packet = {};
  const size_t cabecalho = offsetof(Packet, subpacket);
  if (!leExato(&packet, cabecalho)) {
    Serial.println("[RX] Cabecalho incompleto; pacote descartado.");
    descartaUART();
    return;
  }

  // Nunca le alem do vetor, mesmo que qntd_medicoes chegue corrompido
  const int qntd = packet.qntd_medicoes;
  if (qntd < 1 || qntd > BUFFER_SIZE) {
    Serial.printf("[RX] no=%u: quantidade invalida (%d); pacote descartado.\n", packet.senderAddress, qntd);
    descartaUART();
    return;
  }
  if (!leExato(packet.subpacket, qntd * sizeof(SubPacket))) {
    Serial.printf("[RX] no=%u: pacote incompleto (%d medicoes esperadas); descartado.\n", packet.senderAddress, qntd);
    descartaUART();
    return;
  }
  uint8_t rssiBruto = 0;
  const bool temRssi = leExato(&rssiBruto, 1);
  // Manual do E220: RSSI (dBm) = -(256 - valor).
  const float rssi = -(256.0f - rssiBruto);

  Serial.printf("[RX] Pacote recebido: no=%u, medicoes=%d, bytes=%u, rssi=%s\n",
                packet.senderAddress, qntd, (unsigned)(cabecalho + qntd * sizeof(SubPacket)),
                temRssi ? String(rssi, 0).c_str() : "ausente");

  // JsonDocument (ArduinoJson v7) cresce sob demanda: 16 medicoes x 6 temperaturas
  // nao cabem nos 512 bytes do StaticJsonDocument antigo
  JsonDocument doc;
  doc["senderAddress"] = packet.senderAddress;
  doc["gateway_id"] = LAB_GATEWAY_ID;
  if (temRssi) doc["rssi"] = rssi;

  // Tratamento de dados da temperatura - no pacote, a temperatura vem como int16_t, representada
  // em quantidades de fracoes de 1/128 graus Celsius
  JsonArray medicoes = doc["medicoes"].to<JsonArray>();
  for (int j = 0; j < qntd; j++) {
    JsonObject m = medicoes.add<JsonObject>();
    // medicao j foi feita (qntd-1-j) ciclos antes da chegada do pacote
    m["idade_min"] = (qntd - 1 - j) * INTERVALO_MIN;
    for (int i = 0; i < 6; i++) {
      String key = "temp_ds" + String(i + 1);
      m[key] = packet.subpacket[j].digTemperature[i] / 128.0f;
    }
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] Pacote LoRa recebido, mas Wi-Fi indisponivel; lote nao foi enviado ao backend.");
    return;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String json;
  serializeJson(doc, json);
  int httpCode = http.POST(json);

  Serial.printf("[HTTP] no=%u gateway=%s medicoes=%d status=%d\n",
                packet.senderAddress, LAB_GATEWAY_ID, qntd, httpCode);
  if (httpCode == 201) {
    Serial.println("[HTTP] Gravacao confirmada pelo backend. Confira o ponto no dashboard.");
  } else {
    Serial.println("[HTTP] Sem confirmacao de gravacao. Confira rede, LAB_SENSOR_ID (lista de nos) e LAB_GATEWAY_ID.");
    if (httpCode > 0) Serial.println(http.getString());
  }
  http.end();
}
