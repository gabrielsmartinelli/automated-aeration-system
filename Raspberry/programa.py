import sys, threading, time
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QDoubleSpinBox,
    QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
import comunicacao


class RadioThread(threading.Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.running = True

    def run(self):
        comunicacao.setup()
        while self.running:
            data = comunicacao.get_data()
            if data:
                self.callback(*data)
            time.sleep(0.1)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Main")
        self.setWindowTitle("Painel de Controle")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()  # 1920x1080

        # ==================== VARIÁVEIS ====================
        config = comunicacao.load_config()
        self.thresholds = config["thresholds"]
        self.mask = config["manual_mask"]
        self.auto_mask = 0
        self.status_atual = [None] * 4

        # ==================== TÍTULO PRINCIPAL ====================
        titulo = QLabel("Painel de Controle")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 46px;
            font-weight: bold;
            color: white;
            margin-top: 15px;
        """)

        # ==================== OXIGÊNIO E TEMPERATURA ====================
        info_layout = QHBoxLayout()
        info_layout.setSpacing(600)
        info_layout.setAlignment(Qt.AlignCenter)

        def criar_card_sensor(titulo, unidade, cor):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: black;
                    border: 2px solid white;
                    border-radius: 20px;
                }
            """)
            frame.setFixedSize(420, 120)

            layout = QVBoxLayout(frame)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(4)
            layout.setAlignment(Qt.AlignCenter)

            lbl_titulo = QLabel(titulo)
            lbl_titulo.setAlignment(Qt.AlignCenter)
            lbl_titulo.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {cor}; border: none;")

            lbl_valor = QLabel(f"--.- {unidade}")
            lbl_valor.setAlignment(Qt.AlignCenter)
            lbl_valor.setStyleSheet(f"font-size: 34px; font-weight: bold; color: {cor}; border: none;")

            layout.addWidget(lbl_titulo)
            layout.addWidget(lbl_valor)

            return frame, lbl_valor

        # Criação dos dois cards
        card_ox, self.label_ox = criar_card_sensor("Oxigênio", "mg/L", "#00ffea")
        card_temp, self.label_temp = criar_card_sensor("Temperatura", "°C", "#ff8800")

        # Adiciona ambos lado a lado
        info_layout.addWidget(card_ox)
        info_layout.addWidget(card_temp)

        # ==================== GRID PRINCIPAL ====================
        grid = QGridLayout()
        grid.setHorizontalSpacing(80)
        grid.setVerticalSpacing(80)
        grid.setContentsMargins(50, 50, 50, 50)

        # ---- Títulos das linhas (coluna 0) ----
        label_manual = QLabel("Acionamento\nManual")
        label_auto = QLabel("Acionamento\npor Oxigênio")
        label_status = QLabel("Status\ndos Aeradores")
        label_manual.setContentsMargins(0, 160, 0, 0)  
        label_auto.setContentsMargins(0, 50, 0, 0)    
        for row, lbl in enumerate([label_manual, label_auto, label_status]):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 28px; color: white; font-weight: bold;")
            grid.addWidget(lbl, row + 1, 0, alignment=Qt.AlignCenter)

        # ---- Criação dos cards dos aeradores (colunas 1 a 4) ----
        self.buttons = []
        self.spinboxes = []
        self.status_labels = []

        for col in range(4):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: black;
                    border: 3px solid white;
                    border-radius: 20px;
                }
            """)
            card_layout = QVBoxLayout()
            card_layout.setAlignment(Qt.AlignCenter)
            card_layout.setSpacing(80)
            card_layout.setContentsMargins(20, 25, 20, 25)

            # -------- Título do aerador --------
            titulo_aerador = QLabel(f"Aerador {col + 1}")
            titulo_aerador.setAlignment(Qt.AlignCenter)
            titulo_aerador.setStyleSheet("font-size: 28px; color: white; font-weight: bold; border: none;")
            card_layout.addWidget(titulo_aerador)

            # -------- Linha 1: Acionamento manual --------
            estado = (self.mask >> col) & 1
            btn = QPushButton("ON" if estado else "OFF")
            btn.setCheckable(True)
            btn.setChecked(bool(estado))
            btn.setMinimumSize(220, 100)
            btn.setStyleSheet(self._btn_style(btn.isChecked(), bordered=True))
            btn.clicked.connect(lambda checked, n=col: self.toggle_aerador(n, checked))
            self.buttons.append(btn)
            card_layout.addWidget(btn, alignment=Qt.AlignCenter)

            # -------- Linha 2: Acionamento por oxigênio --------
            ox_layout = QVBoxLayout()
            ox_layout.setSpacing(10)
            ox_layout.setAlignment(Qt.AlignCenter)

            label_min = QLabel("Mínimo")
            label_min.setAlignment(Qt.AlignCenter)
            label_min.setStyleSheet("font-size: 20px; color: white; border: none; margin-bottom: 5px;")
            ox_layout.addWidget(label_min)

            spin_layout = QHBoxLayout()
            spin_layout.setSpacing(12)
            spin_layout.setAlignment(Qt.AlignCenter)

            btn_minus = QPushButton("–")
            btn_plus = QPushButton("+")
            for b in (btn_minus, btn_plus):
                b.setFixedSize(60, 80)
                b.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.15);
                        color: white;
                        font-size: 36px;
                        font-weight: bold;
                        border-radius: 10px;
                        border: 2px solid white;
                    }
                    QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
                """)

            spin = QDoubleSpinBox()
            spin.setRange(0.00, 20.00)
            spin.setDecimals(2)
            spin.setSingleStep(0.10)
            spin.setValue(self.thresholds[col])
            spin.setFixedSize(120, 80)
            spin.setAlignment(Qt.AlignCenter)
            spin.setFont(QFont("Arial", 24, QFont.Bold))
            spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
            spin.setStyleSheet("""
                QDoubleSpinBox {
                    color: white;
                    background-color: rgba(0, 0, 0, 200);
                    border: 2px solid white;
                    border-radius: 10px;
                }
            """)
            spin.valueChanged.connect(self.save_config)
            btn_minus.clicked.connect(lambda _, s=spin: s.setValue(s.value() - s.singleStep()))
            btn_plus.clicked.connect(lambda _, s=spin: s.setValue(s.value() + s.singleStep()))

            spin_layout.addWidget(btn_minus)
            spin_layout.addWidget(spin)
            spin_layout.addWidget(btn_plus)
            ox_layout.addLayout(spin_layout)

            card_layout.addLayout(ox_layout)
            self.spinboxes.append(spin)

            # -------- Linha 3: Status --------
            status = QLabel("DESLIGADO")
            status.setAlignment(Qt.AlignCenter)
            status.setFixedSize(240, 100)
            status.setStyleSheet(self._status_style(False, bordered=True))
            self.status_labels.append(status)
            card_layout.addWidget(status, alignment=Qt.AlignCenter)

            card.setLayout(card_layout)
            grid.addWidget(card, 1, col + 1, 3, 1, alignment=Qt.AlignCenter)

        # ==================== LAYOUT PRINCIPAL ====================
        main_layout = QVBoxLayout()
        main_layout.setSpacing(60)
        main_layout.addSpacerItem(QSpacerItem(10, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addWidget(titulo)
        main_layout.addLayout(info_layout)
        main_layout.addLayout(grid)
        main_layout.addSpacerItem(QSpacerItem(10, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(main_layout)

        # ==================== FUNDO ====================
        self.setStyleSheet("""
            QWidget#Main {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #001F3F, stop:1 #003C80);
            }
        """)

        # ==================== THREAD ====================
        self.radio_thread = RadioThread(self.update_data)
        self.radio_thread.start()

    # =====================================================
    def _btn_style(self, on, bordered=False):
        border = "border: 2px solid white;" if bordered else ""
        if on:
            return f"""
                QPushButton {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #007A33, stop:1 #00C851);
                    color: white;
                    font-weight: bold;
                    font-size: 24px;
                    border-radius: 12px;
                    {border}
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #C62828, stop:1 #E53935);
                    color: white;
                    font-weight: bold;
                    font-size: 24px;
                    border-radius: 12px;
                    {border}
                }}
            """

    def _status_style(self, ligado, bordered=False):
        border = "border: 2px solid white;" if bordered else ""
        return f"""
            QLabel {{
                background-color: {'#00C851' if ligado else '#C62828'};
                color: white;
                font-weight: bold;
                font-size: 26px;
                border-radius: 12px;
                {border}
            }}
        """

    # =====================================================
    def update_data(self, ox, temp):
        """Atualiza valores e status conforme máscara final."""
        self.label_ox.setText(f"{ox:.2f} mg/L")
        self.label_temp.setText(f"{temp:.2f} °C")

        thresholds = [spin.value() for spin in self.spinboxes]
        final_mask, self.auto_mask = comunicacao.calculate_mask(ox, thresholds, self.mask)
        comunicacao.send_mask(final_mask)

        for i, lbl in enumerate(self.status_labels):
            ligado = bool((final_mask >> i) & 1)
            if ligado != self.status_atual[i]:
                self.status_atual[i] = ligado
                lbl.setText("LIGADO" if ligado else "DESLIGADO")
                lbl.setStyleSheet(self._status_style(ligado, bordered=True))

    def toggle_aerador(self, index, state):
        if state:
            self.mask |= (1 << index)
            self.buttons[index].setText("ON")
        else:
            self.mask &= ~(1 << index)
            self.buttons[index].setText("OFF")
        self.buttons[index].setStyleSheet(self._btn_style(state, bordered=True))
        self.save_config()

    def save_config(self):
        thresholds = [spin.value() for spin in self.spinboxes]
        comunicacao.save_config(thresholds, self.mask)

    def closeEvent(self, event):
        self.radio_thread.running = False
        self.radio_thread.join(timeout=1)
        comunicacao.save_config([spin.value() for spin in self.spinboxes], self.mask)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(5, 20, 50))
    palette.setColor(QPalette.WindowText, QColor("white"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
