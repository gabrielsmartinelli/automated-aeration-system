#ifndef SENSOR_H
#define SENSOR_H

#include <Arduino.h>

// Estrutura lida no sensor,
// valores de oxigênio e temperatura,
// ambos em ponto flutuante
struct ProbeData {
  float oxygen;
  float temperature;
};

// Função que inicializa o módulo MAX485
void sensorInit();

// Função de leitura dos dados do sensor
void sensorRead(ProbeData &data);

#endif

