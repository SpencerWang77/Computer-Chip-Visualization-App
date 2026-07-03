from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout)


class UploadSection(QGroupBox):
    """File picker plus die/lead-frame parameters."""

    def __init__(self, parent=None):
        super().__init__("Import Data", parent)
        self.file_label = None
        self.upload_btn = None
        self.die_width_input = None
        self.die_height_input = None
        self.pin_count_input = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
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

        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 20px;
                color: #7f8c8d;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.file_label)

        self.upload_btn = QPushButton("Select Excel File")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1a5276;
            }
        """)
        layout.addWidget(self.upload_btn)

        self._add_frame_settings(layout)

    def set_file_selected(self, file_name: str):
        self.file_label.setText("Selected: " + file_name)
        self.file_label.setStyleSheet("""
            QLabel {
                background-color: #d5f4e6;
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 20px;
                color: #27ae60;
                font-size: 12px;
                font-weight: bold;
            }
        """)

    def get_upload_button(self):
        return self.upload_btn

    def _add_frame_settings(self, parent_layout):
        frame_title = QLabel("Package Settings")
        frame_title.setAlignment(Qt.AlignCenter)
        frame_title.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
                font-size: 12px;
                font-weight: bold;
                margin-top: 15px;
            }
        """)
        parent_layout.addWidget(frame_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        input_style = """
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """

        self.die_width_input = QLineEdit()
        self.die_width_input.setPlaceholderText("e.g. 5000")
        self.die_width_input.setText("3475.8")
        self.die_width_input.setValidator(QDoubleValidator(0.1, 100000.0, 2))
        self.die_width_input.setStyleSheet(input_style)
        form_layout.addRow("Die width (µm):", self.die_width_input)

        self.die_height_input = QLineEdit()
        self.die_height_input.setPlaceholderText("e.g. 5000")
        self.die_height_input.setText("3105")
        self.die_height_input.setValidator(QDoubleValidator(0.1, 100000.0, 2))
        self.die_height_input.setStyleSheet(input_style)
        form_layout.addRow("Die height (µm):", self.die_height_input)

        self.pin_count_input = QLineEdit()
        self.pin_count_input.setPlaceholderText("auto-detected from the file")
        self.pin_count_input.setValidator(QIntValidator(4, 1000))
        self.pin_count_input.setStyleSheet(input_style)
        form_layout.addRow("Lead frame pin count:", self.pin_count_input)

        info_label = QLabel("* Pin count is auto-filled from the highest LF.<n>\n"
                            "  in the file (rounded up to a multiple of 4);\n"
                            "  you can override it before visualizing.")
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                font-style: italic;
                padding: 5px;
            }
        """)
        form_layout.addRow("", info_label)

        parent_layout.addLayout(form_layout)

    def set_pin_count(self, pin_count: int):
        """Pre-fill the pin count (auto-detected from the loaded file)."""
        if pin_count > 0:
            self.pin_count_input.setText(str(pin_count))

    def get_frame_parameters(self):
        try:
            die_width = float(self.die_width_input.text()) if self.die_width_input.text() else None
            die_height = float(self.die_height_input.text()) if self.die_height_input.text() else None
            pin_count = int(self.pin_count_input.text()) if self.pin_count_input.text() else None
            return {
                'die_width': die_width,
                'die_height': die_height,
                'pin_count': pin_count,
            }
        except ValueError:
            return None
