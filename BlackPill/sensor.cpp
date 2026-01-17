#include "sensor.h"
#include "pins.h"

// USART1 (PA9=TX, PA10=RX)
#define SENSOR_SERIAL Serial1

// ID do escravo
#define SLAVE_ID 1

// Endereço para leitura do oxigênio
#define REG_O2_START 2091

// Endereço para leitura da temperatura
#define REG_TEMP_START 2411

// Quantidade de registradores a serem lidos
#define REG_COUNT 2

// Tempo máximo de espera pela resposta em milissegundos
#define MODBUS_TIMEOUT  800


// Função que calcula o CRC-16 usado no protocolo Modbus
// Recebe um ponteiro para os dados (data) e o comprimento em bytes (length)
static uint16_t modbusCRC(const uint8_t *data, uint16_t length) {

  // Inicializa o valor do CRC com 0xFFFF (valor padrão do algoritmo Modbus)
  uint16_t crc = 0xFFFF;

  // Percorre todos os bytes do vetor de dados
  for (uint16_t pos = 0; pos < length; pos++) {

    // Faz um XOR entre o byte atual e os 8 bits menos significativos do CRC
    // Isso injeta o novo byte no cálculo do CRC
    crc ^= (uint16_t)data[pos];

    // Processa cada um dos 8 bits do byte
    for (uint8_t i = 0; i < 8; i++) {

      // Verifica se o bit menos significativo (LSB) do CRC é 1
      if (crc & 1)
        // Se for 1: desloca o CRC para a direita e aplica o polinômio 0xA001
        crc = (crc >> 1) ^ 0xA001;
      else
        // Se for 0: apenas desloca o CRC para a direita
        crc = crc >> 1;
    }
  }

  // Retorna o valor final do CRC calculado (16 bits)
  return crc;
}

// Função para habilitar a transmissão
static void setTX() { digitalWrite(MAX485_RE_DE, HIGH); }

// Função para habilitar a recepção
static void setRX() { digitalWrite(MAX485_RE_DE, LOW); }

// Função para ler um registrador Modbus contendo um valor float (2 registradores de 16 bits)
static bool readFloatRegister(uint16_t regAddr, float &value) {

  // Limpa o buffer serial da sonda (descarta bytes antigos)
  while (SENSOR_SERIAL.available()) SENSOR_SERIAL.read();

  // Montagem do frame Modbus de requisição (8 bytes)
  uint8_t frame[8];
  frame[0] = SLAVE_ID;                // ID do escravo (endereço do dispositivo Modbus)
  frame[1] = 0x03;                    // Código da função: 0x03 = Ler Holding Registers
  frame[2] = (regAddr >> 8) & 0xFF;   // Byte alto do endereço inicial do registrador
  frame[3] = regAddr & 0xFF;          // Byte baixo do endereço inicial
  frame[4] = 0x00;                    // Byte alto da quantidade de registradores a ler
  frame[5] = REG_COUNT;               // Byte baixo da quantidade de registradores
  uint16_t crc = modbusCRC(frame, 6); // Calcula o CRC-16 Modbus dos 6 primeiros bytes
  frame[6] = crc & 0xFF;              // Byte baixo do CRC
  frame[7] = (crc >> 8) & 0xFF;       // Byte alto do CRC

  // Envio do frame Modbus via RS-485
  setTX();                            // Habilita modo de transmissão no MAX485 (DE/RE = HIGH)
  delayMicroseconds(100);             // Breve atraso para estabilizar o driver
  SENSOR_SERIAL.write(frame, 8);      // Envia os 8 bytes da requisição
  SENSOR_SERIAL.flush();              // Aguarda a conclusão da transmissão
  setRX();                            // Retorna para o modo de recepção (DE/RE = LOW)

  // Aguarda a resposta do escravo
  unsigned long start = millis();     

  // Espera até receber pelo menos 7 bytes ou atingir o tempo limite
  while (SENSOR_SERIAL.available() < 7 && (millis() - start < MODBUS_TIMEOUT)) {
    delay(1);
  }

  // Se nenhum byte chegou dentro do tempo limite → erro
  if (SENSOR_SERIAL.available() == 0) { return false; }

  delay(50); // Pequeno atraso para garantir que o frame completo chegou

  // Buffer para armazenar a resposta recebida
  uint8_t resp[16];

  // Lê todos os bytes disponíveis
  size_t len = SENSOR_SERIAL.readBytes(resp, sizeof(resp));

  // Verifica se o frame tem tamanho mínimo e função/código corretos
  if (len < 7 || resp[0] != SLAVE_ID || resp[1] != 0x03) { return false; }

  // Validação do CRC
  uint16_t crcRx = (resp[len - 1] << 8) | resp[len - 2];   // CRC recebido (2 últimos bytes)
  uint16_t crcCalc = modbusCRC(resp, len - 2);             // CRC calculado localmente
  if (crcRx != crcCalc) { return false; }                  // Se diferentes → erro de transmissão

  // Verifica se o número de bytes de dados é suficiente para formar um float (4 bytes)
  uint8_t byteCount = resp[2];
  if (byteCount < 4) { return false; }

  // Conversão CDAB (formato float usado por muitos dispositivos Modbus)
  // Rearranja os bytes na ordem correta
  uint8_t a = resp[3];
  uint8_t b = resp[4];
  uint8_t c = resp[5];
  uint8_t d = resp[6];

  // Combina os bytes conforme o padrão CDAB → (C D A B)
  uint32_t raw = ((uint32_t)c << 24) | ((uint32_t)d << 16) | ((uint32_t)a << 8) | b;

  // Copia os 4 bytes (inteiro) para a variável float final
  memcpy(&value, &raw, sizeof(float));

  // Se tudo deu certo, retorna verdadeiro
  return true;
}

// Inicializa o MAX485
void sensorInit() {
  pinMode(MAX485_RE_DE, OUTPUT);
  setRX();
  SENSOR_SERIAL.begin(19200, SERIAL_8N2);
}

// Função de leitura dos valores do sensor
void sensorRead(ProbeData &data) {
  
  // Variável que guarda o instante (em ms) da última leitura bem-sucedida
  static unsigned long lastSuccess = 0;

  // Variáveis temporárias para armazenar os valores lidos via Modbus
  float o2 = 0, temp = 0;

  // Faz a leitura do valor de oxigênio
  bool readOxygen = readFloatRegister(REG_O2_START, o2);

  // Pequeno atraso entre as duas leituras, para evitar sobrecarga no barramento
  delay(250);

  // Faz a leitura da temperatura
  bool readTemperature = readFloatRegister(REG_TEMP_START, temp);

  // Caso ambas as leituras tenham sido bem-sucedida
  if (readOxygen && readTemperature) {
    data.oxygen = o2;          // Atualiza a estrutura com o valor de oxigênio
    data.temperature = temp;   // Atualiza a estrutura com o valor de temperatura
    lastSuccess = millis();    // Registra o instante da última leitura válida
  }

  // Caso uma ou ambas as leituras falhem
  else {
    // Verifica se já se passaram 5 minutos desde a última leitura bem-sucedida
    if (millis() - lastSuccess >= 300000UL) {
      // Se passou muito tempo sem sucesso, zera os valores por segurança
      data.oxygen = 0.0;
      data.temperature = 0.0;
    }
  }
}



