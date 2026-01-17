#include "radio.h"
#include <RF24.h>
#include "pins.h"

// Instância do rádio
RF24 radio(NRF_CE, NRF_CSN);

// Endereços (pipes) usados para comunicação
const byte addr_tx[6] = "RPi58";   // Raspberry Pi (transmissão)
const byte addr_rx[6] = "Bp32A";   // Black Pill   (recepção)

// ---------------------------------------------------------------------------
// Inicialização do rádio
// ---------------------------------------------------------------------------

void radioInit() {

  // Define o LED embutido como saída
  pinMode(STATUS_LED, OUTPUT);

  // Enquanto o rádio não conseguir inicializar, o LED pisca
  // com intervalo de 1 segundo
  while (!radio.begin()) {
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    delay(1000);
  }

  // Depois que inicializar, o LED fica aceso
  digitalWrite(STATUS_LED, LOW);

  // Amplificador de Potência deve operar no nível máximo
  radio.setPALevel(RF24_PA_MAX);

  // Taxa de dados em 250 kbps para maior alcance
  radio.setDataRate(RF24_250KBPS);

  // Canal de comunicação 100 (2,5 GHz)
  radio.setChannel(100);

  // Verificação de Redundância Cíclica de 16 bits (2 bytes)
  radio.setCRCLength(RF24_CRC_16);

  // Envia automaticamenteo ACK ao receber um payload
  radio.setAutoAck(true);

  // 15 tentativas extras de envio dos pacotes 
  // com delay de 4 ms entre cada uma
  radio.setRetries(15, 15);

  // Sai do modo de recepção
  radio.stopListening();
}

// ---------------------------------------------------------------------------
// Entra no modo de transmissão
// ---------------------------------------------------------------------------
void enterTX() {
  radio.stopListening();           // Sai do modo de recepção
  radio.openWritingPipe(addr_tx);  // Abre o pipe de transmissão
}

// ---------------------------------------------------------------------------
// Entra no modo de recepção
// ---------------------------------------------------------------------------
void enterRX() {
  radio.openReadingPipe(1, addr_rx);  // Abre o pipe de recepção
  radio.startListening();             // Habilita a recepção
}

// ---------------------------------------------------------------------------
// Envia os dados de oxigênio e temperatura
// ---------------------------------------------------------------------------
void sendSensorData(const SensorData &data) {
  // envia o payload com os dados e o tamanho deles em bytes
  radio.write(&data, sizeof(data));
}

// ---------------------------------------------------------------------------
// Reecebe a máscara dos relés dentro do tempo limite
// ---------------------------------------------------------------------------
bool receiveRelayMask(uint8_t &mask, unsigned long timeout) {

  // Intervalo de tempo em milissegundos que o microcontrolador está ligado
  unsigned long start = millis();

  // Enquanto não se passar o tempo limite, tenta receber dados via rádio
  while (millis() - start < timeout) {

    // Se o rádio está comunicando, lê a máscara e o tamanho dela
    // e retorna verdadeiro
    if (radio.available()) {
      radio.read(&mask, sizeof(mask));
      return true;
    }
  }

  // Se não conseguir ler dentro do tempo limite, retorna falso
  return false;
}