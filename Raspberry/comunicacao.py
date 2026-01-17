from pyrf24 import RF24, RF24_PA_MAX, RF24_250KBPS, RF24_CRC_16
import struct, time, json, os, threading

# ==================== LOCK PARA ACESSO AO RÁDIO ====================
# Impede que duas threads chamem funções RF24 ao mesmo tempo
radio_lock = threading.Lock()

# ==================== CONFIGURAÇÃO RF24 ====================
radio = RF24(25, 0)  # CE=GPIO25, CSN=SPI0-CE0
ADDR_RX = b"RPi58"
ADDR_TX = b"Bp32A"
payload_format = "<ff"
payload_size = struct.calcsize(payload_format)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_oxigenio.json")

# ==================== FUNÇÕES RF24 ====================
def enter_tx():
    radio.stopListening()
    radio.openWritingPipe(ADDR_TX)

def enter_rx():
    radio.openReadingPipe(1, ADDR_RX)
    radio.startListening()

def setup():
    with radio_lock:
        if not radio.begin():
            raise SystemExit("radio.begin() falhou.")
        radio.setPALevel(RF24_PA_MAX)
        radio.setDataRate(RF24_250KBPS)
        radio.setChannel(100)
        radio.setCRCLength(RF24_CRC_16)
        radio.setAutoAck(True)
        radio.setRetries(15, 15)
        enter_rx()
        print("Inicialização concluída, aguardando dados...")

def get_data():
    """Verifica se há dados disponíveis e retorna (oxigênio, temperatura) ou None."""
    with radio_lock:
        if radio.available():
            data = radio.read(payload_size)
            ox, temp = struct.unpack(payload_format, data)
            return ox, temp
    return None

def send_mask(mask: int):
    """Envia uma máscara de 1 byte para a Black Pill logo após RX, com até 5 tentativas."""
    with radio_lock:
        for attempt in range(5):
            enter_tx()
            ok = radio.write(bytes([mask & 0xFF]))
            enter_rx()
            if ok:
                print(f"TX -> Máscara {bin(mask)} enviada com ACK (tentativa {attempt+1})")
                return True
            time.sleep(0.05)

    print("TX -> Falha ao enviar máscara (sem ACK após 5 tentativas).")
    return False

# ==================== CONFIGURAÇÃO LOCAL ====================
def load_config():
    """Carrega limiares e estado dos aeradores."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return {
                    "thresholds": data.get("aeradores", [5.0, 5.0, 5.0, 5.0]),
                    "manual_mask": data.get("mask", 0)
                }
        except Exception as e:
            print(f"Erro ao carregar {CONFIG_FILE}: {e}")
    return {"thresholds": [5.0, 5.0, 5.0, 5.0], "manual_mask": 0}

def save_config(thresholds, manual_mask):
    """Salva limiares e estado dos aeradores."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"aeradores": thresholds, "mask": manual_mask}, f, indent=2)
        print(f"Configuração salva: {thresholds}, máscara {bin(manual_mask)}")
    except Exception as e:
        print(f"Erro ao salvar {CONFIG_FILE}: {e}")

# ==================== LÓGICA DE CONTROLE ====================
def calculate_mask(o2_value, thresholds, manual_mask=0):
    """Calcula máscara automática baseada em O2 e limiares."""
    o2_value = round(o2_value, 2)  # ← arredonda para duas casas decimais
    auto_mask = 0
    for i, limiar in enumerate(thresholds):
        if o2_value <= limiar:
            auto_mask |= (1 << i)
    final_mask = auto_mask | manual_mask
    return final_mask, auto_mask

if __name__ == "__main__":
    setup()
    while True:
        data = get_data()
        if data:
            ox, temp = data
            print(f"O2={ox:.2f}, Temp={temp:.2f}")
        time.sleep(0.1)
