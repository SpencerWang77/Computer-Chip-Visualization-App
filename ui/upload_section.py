from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import (QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout, QWidget)


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

        # Die sizes are read per-die from the file; these are optional.
        # Lead frame pins: (per horizontal edge) × (per vertical edge).
        self.pin_x_input = QLineEdit()
        self.pin_x_input.setValidator(QIntValidator(1, 1000))
        self.pin_x_input.setStyleSheet(input_style)
        self.pin_y_input = QLineEdit()
        self.pin_y_input.setValidator(QIntValidator(1, 1000))
        self.pin_y_input.setStyleSheet(input_style)
        form_layout.addRow("Pins per edge (top/bot × left/right):",
                           self._pair_row(self.pin_x_input, self.pin_y_input))

        # VSS ring outer size: width × height (µm).
        self.ring_w_input = QLineEdit()
        self.ring_w_input.setPlaceholderText("auto")
        self.ring_w_input.setValidator(QDoubleValidator(1.0, 1000000.0, 2))
        self.ring_w_input.setStyleSheet(input_style)
        self.ring_h_input = QLineEdit()
        self.ring_h_input.setPlaceholderText("auto")
        self.ring_h_input.setValidator(QDoubleValidator(1.0, 1000000.0, 2))
        self.ring_h_input.setStyleSheet(input_style)
        form_layout.addRow("VSS ring size W × H (µm):",
                           self._pair_row(self.ring_w_input, self.ring_h_input))

        info_label = QLabel("* Die sizes are read from the file; no need to enter.\n"
                            "* Pins per edge: first = each of top/bottom, second =\n"
                            "  each of left/right (a rectangular package can differ).\n"
                            "* Ring size is the outer W × H. Leave a field empty for\n"
                            "  a square / spacious default large enough to move dies.")
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

    @staticmethod
    def _pair_row(field_a, field_b):
        """A horizontal 'a × b' row of two inputs."""
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)
        times = QLabel("×")
        times.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        row.addWidget(field_a)
        row.addWidget(times)
        row.addWidget(field_b)
        container = QWidget()
        container.setLayout(row)
        return container

    def set_pin_count(self, pin_count: int):
        """Pre-fill the per-edge pin counts (square) from the auto-detected
        total (e.g. 120 -> 30 × 30)."""
        if pin_count and pin_count >= 4:
            per_edge = round(pin_count / 4)
            self.pin_x_input.setText(str(per_edge))
            self.pin_y_input.setText(str(per_edge))

    def set_pins(self, pin_x, pin_y):
        """Pre-fill the per-edge pin counts (e.g. from a saved layout)."""
        if pin_x:
            self.pin_x_input.setText(str(int(pin_x)))
        if pin_y:
            self.pin_y_input.setText(str(int(pin_y)))

    def set_ring_size(self, width, height):
        """Pre-fill the ring size fields (e.g. from a saved layout)."""
        if width:
            self.ring_w_input.setText(f"{float(width):g}")
        if height:
            self.ring_h_input.setText(f"{float(height):g}")

    def get_frame_parameters(self):
        try:
            def num(widget, cast):
                text = widget.text().strip()
                return cast(text) if text else None

            pin_x = num(self.pin_x_input, int)
            pin_y = num(self.pin_y_input, int)
            # Default to square if only one side is given.
            if pin_x is None and pin_y is not None:
                pin_x = pin_y
            if pin_y is None and pin_x is not None:
                pin_y = pin_x

            ring_w = num(self.ring_w_input, float)
            ring_h = num(self.ring_h_input, float)
            if ring_w is None and ring_h is not None:
                ring_w = ring_h
            if ring_h is None and ring_w is not None:
                ring_h = ring_w

            return {
                'pin_x': pin_x,
                'pin_y': pin_y,
                'ring_w': ring_w,
                'ring_h': ring_h,
            }
        except ValueError:
            return None
