#include "radio.h"
#include "relay.h"
#include "sensor.h"

// VAlores de oxigênio e temperatura lidos pelo sensor
SensorData txData;

// Valores de oxigênio e temperatura enviados via rádio
ProbeData probe;


// Função de leitura dos dados do sensor
void readSensorData() {

  // Realiza a leitura dos dados do sensor
  sensorRead(probe);

  // Atualiza os valores para transmissão via rádio
  txData.oxygen = probe.oxygen;
  txData.temperature = probe.temperature;
}


// Executa as funções de inicialização
void setup() {
  relayInit();
  radioInit();
  sensorInit();
}

void loop() {

  // Executa a função de leitura dos valores do sensor
  readSensorData();

  // Entra em modo de transmissão e envia os dados via rádio
  enterTX();
  sendSensorData(txData);

  // Entra em modo de recepção por até 1 segundo
  enterRX();

  // Inicializa a máscara dos relés em zero
  uint8_t relayMask = 0;

  // Se receber uma máscara via rádio, aplica ela
  if (receiveRelayMask(relayMask, 1000)) {
    relayApplyMask(relayMask);
  }

  // Atualiza estados dos relés
  relayUpdate();

  // Intervalo de meio segundo antes de reiniciar o ciclo
  delay(500);
}
