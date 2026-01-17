#ifndef RADIO_H
#define RADIO_H

#include <Arduino.h>

// Estrutura enviada no payload do rádio,
// valores de oxigênio e temperatura,
// ambos em ponto flutuante
struct SensorData {
  float oxygen;
  float temperature;
};

// Função responsável por inicializar o rádio
// com os atributos desejados
void radioInit();

// Função para definir o rádio no modo de transmissão
void enterTX();

// Função para definir o rádio no modo de recepção
void enterRX();

// Função de envio dos valores via rádio
void sendSensorData(const SensorData &data);

// Função de leitura do valor de máscara dos relés pelo rádio
bool receiveRelayMask(uint8_t &mask, unsigned long timeout);

#endif

