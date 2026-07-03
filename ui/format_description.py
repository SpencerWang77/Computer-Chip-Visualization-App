from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QLabel, QVBoxLayout


class FormatDescription(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("File Format", parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #27ae60;
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 15px;
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background: white;
            }
        """)

        layout = QVBoxLayout(self)

        format_text = QLabel("""
Supported file format:
• Excel file (.xlsx, .xls) with a worksheet named "connect"
• Columns: Die Pad No, Pad name, X-coord, Y-coord, X open, Y open, Net Name, Bonding

Data layout:
• Row 1: column headers
• Row 2: units / remarks
• Row 3 onward: pad data (coordinates in µm, numeric)

Bonding column values:
• LF.<n> — wire bonded to lead frame pin n
• VSS_ring — wire bonded to the VSS ring (E-PAD ring)
• Not Bond — no wire
• SOC.<n> / PSRAM.<n> / DDRA.<n> / DDRB.<n> / ROM.<n> — die-to-die bond
        """)
        format_text.setStyleSheet("color: #34495e; font-size: 11px; line-height: 1.6;")
        format_text.setAlignment(Qt.AlignLeft)
        layout.addWidget(format_text)
