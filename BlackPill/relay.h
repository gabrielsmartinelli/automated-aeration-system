#ifndef RELAY_H
#define RELAY_H

#include <Arduino.h>

// Função de inicialização para os relés
void relayInit();

// Função para aplicar uma máscara às saídas
void relayApplyMask(uint8_t mask);

// Função que atualiza os estados dos relés
void relayUpdate();

#endif
