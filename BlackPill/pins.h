#ifndef PROTOTYPE_PINS_H
#define PROTOTYPE_PINS_H

// nRF24L01+
#define NRF_CE  PB0         // Chip Enable
#define NRF_CSN PB1         // Chip Select

// MAX485
#define MAX485_DI    PA9    // Driver Input
#define MAX485_RO    PA10   // Receiver Output

// Receiver Enable e Driver Enable em curto-circuito
#define MAX485_RE_DE PA8 

// Relés
#define RELAY0 PB3
#define RELAY1 PB4
#define RELAY2 PB5
#define RELAY3 PB6

// LED embutido na Black Pill
#define STATUS_LED PC13

#endif
