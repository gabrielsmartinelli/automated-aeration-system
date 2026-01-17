"""
Simulador Modbus RTU da sonda óptica Yokogawa DO71/DO72
--------------------------------------------------------
- Implementa um escravo Modbus RTU via RS-485 (USB/TTL)
- Mapeia registradores 2000–5000 conforme manual
- Valores principais:
    - HR2091: Oxigênio (float, mg/L)
    - HR2411: Temperatura (float, °C)
- Atualiza dinamicamente com teclas ou script externo
"""

# Importa módulos principais do pymodbus para criar um servidor Modbus RTU
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
# Define o tipo de enquadramento (RTU) para o protocolo Modbus
from pymodbus.framer.rtu_framer import ModbusRtuFramer
# Função que inicia o servidor serial síncrono (loop principal)
from pymodbus.server.sync import StartSerialServer
# Thread usada para atualizar os valores em segundo plano
from threading import Thread
# struct para converter floats em bytes (e vice-versa)
import struct
import time

# ================= CONFIGURAÇÕES =================
PORTA_SERIAL = "/dev/ttyUSB0"   # Porta serial física/virtual usada (adaptador RS-485)
BAUDRATE = 19200                # Taxa de transmissão
STOPBITS = 2                    # Número de bits de parada
PARIDADE = "N"                  # Paridade (N = nenhuma)
SLAVE_ID = 1                    # Endereço Modbus do escravo
TIMEOUT = 1                     # Tempo máximo de espera em segundos

UPDATE_INTERVAL = 2.0           # Intervalo entre atualizações automáticas
# =================================================


# --- Funções auxiliares ---


def float_to_regs(value):
    """Converte um valor float em dois registradores Modbus (formato little endian CDAB)"""
    # struct.pack empacota o float em 4 bytes (ordem little endian)
    raw = struct.pack("<f", value)
    # Divide os 4 bytes em dois inteiros de 16 bits
    b = struct.unpack("<HH", raw)
    # Retorna a lista [reg1, reg2] com os dois registradores
    return list(b)


def regs_to_float(reg_hi, reg_lo):
    """Converte dois registradores Modbus (16 bits cada) em um float"""
    # Empacota os dois registradores de volta em 4 bytes
    raw = struct.pack("<HH", reg_hi, reg_lo)
    # Desempacota como float de 32 bits (ordem little endian)
    return struct.unpack("<f", raw)[0]


# --- Inicializa registradores padrão ---
registers = [0] * 5000  # Cria lista simulando 5000 registradores (endereços 0–4999)

# Atribuições fixas de configuração, conforme manual da sonda
registers[2089 - 1] = 0x0080  # Unidade de O2 (mg/L)
registers[2409 - 1] = 0x0004  # Unidade de temperatura (°C)
registers[4095 - 1] = 1       # ID do dispositivo
registers[4101 - 1] = 0x0004  # Baud rate = 19200
registers[3499 - 1] = 1       # Intervalo de atualização (rate)

# Valores iniciais de leitura
O2_value = 0.00
Temp_value = 0.00
# Converte os floats iniciais em dois registradores cada
o2_regs = float_to_regs(O2_value)
t_regs = float_to_regs(Temp_value)
# Salva os registradores equivalentes nos endereços Modbus esperados
registers[2091 - 1] = o2_regs[0]
registers[2091] = o2_regs[1]
registers[2411 - 1] = t_regs[0]
registers[2411] = t_regs[1]

# --- Inicializa contexto Modbus ---
# Cria o "banco de dados" do escravo (holding registers HR 2000–4999)
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(2000, registers[2000:]),  # offset inicial 2000
    zero_mode=False  # False = endereçamento começa em 1 (padrão Modbus)
)
# Cria o contexto do servidor (único escravo neste caso)
context = ModbusServerContext(slaves=store, single=True)


# --- Função de atualização em segundo plano ---
def atualizar_dinamico():
    """Loop contínuo que permite alterar os valores simulados de O2 e temperatura."""
    global O2_value, Temp_value
    while True:
        try:
            # Aguarda entrada do usuário no terminal, ex: "o2=7.8"
            entrada = input("Digite novo valor (ex: o2=7.8 ou t=23.5): ").strip()
            # Atualiza o valor conforme prefixo digitado
            if entrada.startswith("o2="):
                O2_value = float(entrada.split("=")[1])
            elif entrada.startswith("t="):
                Temp_value = float(entrada.split("=")[1])
            else:
                print("Use o2=<valor> ou t=<valor>")
        except Exception:
            # Ignora erros de entrada (ex: linha vazia)
            pass

        # Converte os novos valores em registradores
        o2_regs = float_to_regs(O2_value)
        t_regs = float_to_regs(Temp_value)

        # Atualiza os registradores no contexto Modbus (func. code 3 = holding registers)
        context[0x00].setValues(3, 2091, o2_regs)
        context[0x00].setValues(3, 2411, t_regs)

        # Exibe os valores atualizados no terminal
        print(f"[Atualizado] O2={O2_value:.2f} mg/L | Temp={Temp_value:.2f} °C")
        # Aguarda o intervalo de atualização antes de pedir novo valor
        time.sleep(UPDATE_INTERVAL)


# --- Thread de atualização dinâmica ---
# Cria uma thread daemon (executa em paralelo ao servidor Modbus)
t = Thread(target=atualizar_dinamico, daemon=True)
t.start()

# Informações iniciais impressas no terminal
print(f"\n=== Simulador Yokogawa DO71/DO72 ===")
print(f"Porta: {PORTA_SERIAL} | Baud: {BAUDRATE} | Slave ID: {SLAVE_ID}")
print(f"Registradores ativos: 2000–5000")
print("Digite: o2=<valor> ou t=<valor> para alterar em tempo real.\n")

# --- Inicia servidor Modbus RTU ---
# Inicia o servidor Modbus RTU que responde a requisições na porta serial definida.
# A função StartSerialServer fica em loop infinito até o programa ser encerrado.
StartSerialServer(
    context,                 # Contexto com os registradores (dados do escravo)
    framer=ModbusRtuFramer,  # Define o enquadramento RTU
    port=PORTA_SERIAL,       # Porta serial física
    baudrate=BAUDRATE,       # Baud rate definido
    stopbits=STOPBITS,       # Bits de parada
    parity=PARIDADE,         # Tipo de paridade
    timeout=TIMEOUT,         # Timeout de comunicação
)

