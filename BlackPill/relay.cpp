#include "relay.h"
#include "pins.h"

// Pinos dos relés
const int relayPins[4] = {RELAY0, RELAY1, RELAY2, RELAY3};

// Variáveis dos estados dos relés e de controle de tempo

// Última máscara recebida
static uint8_t currentMask = 0xFF;

// Última máscara aplicada
static uint8_t lastAppliedMask = 0xFF;

// Último instante em que uma máscara foi recebida
static unsigned long lastMaskUpdate = 0;

// último instante no qual um relé foi atualizado
static unsigned long lastRelayUpdate = 0;

// Índice do relé atual
static int currentRelay = 0;

// Status do tempo limite, se foi ativo ou não
static bool timeoutActive = false;

// Intervalo entre atualização dos relés (5 segundos)
const unsigned long RELAY_INTERVAL = 5000UL;

// Tempo limite sem nova máscara (5 minutos)
const unsigned long RELAY_TIMEOUT  = 5UL * 60UL * 1000UL;

// ---------------------------------------------------------------------------
// Inicialização dos relés
// ---------------------------------------------------------------------------
void relayInit() {

  // Coloca todas as saídas em HIGH (relés em NC passam energia)
  for (int i = 0; i < 4; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH);
  }
}

// ---------------------------------------------------------------------------
// Aplicação da máscara
// ---------------------------------------------------------------------------
void relayApplyMask(uint8_t mask) {
  currentMask = mask;
  lastMaskUpdate = millis(); // Atualiza o instante de atualização da máscara
  timeoutActive = false;     // Define que não extrapolou o tempo limite
}

// ---------------------------------------------------------------------------
// Atualização dos relés
// ---------------------------------------------------------------------------
void relayUpdate() {

  // Instante atual desde que o microcontrolador iniciou, em milissegundos
  unsigned long now = millis();

  // Verifica se expirou o tempo limite de 5 minutos,
  // se sim, define as condições para ativar todas as saídas
  if (!timeoutActive && (now - lastMaskUpdate >= RELAY_TIMEOUT)) {

    timeoutActive = true;
    currentRelay = 0;
    lastRelayUpdate = now;
    currentMask = 0xFF;
  }

  // Checa se passou mais de 5 segundos sem atualizar os relés
  if (now - lastRelayUpdate >= RELAY_INTERVAL) {

    // Estado do relé na máscara atual
    bool desiredState = (currentMask >> currentRelay) & 0x01;

    // Estado do relé na última máscara aplicada
    bool currentState = (lastAppliedMask >> currentRelay) & 0x01;

    // Muda o estado apenas se os estados anteriores forem diferentes
    if (desiredState != currentState) {

      digitalWrite(relayPins[currentRelay], desiredState);

      // Atualiza o bit correspondente do relé atual na última máscara aplicada
      if (desiredState)
        lastAppliedMask |= (1 << currentRelay);   // Aplica o valor 1
      else
        lastAppliedMask &= ~(1 << currentRelay);  // Aplica o valor 0
    }

    // Avança para o próximo relé, se passar do último volta no primeiro
    currentRelay++;

    if (currentRelay >= 4) {
      currentRelay = 0;

      // Coloca o status de tempo limite em falso caso esteja como verdadeiro
      if (timeoutActive) {
        timeoutActive = false;
      }
    }

    // Define o instante atual como última atualização dos relés
    lastRelayUpdate = now;
  }
}

