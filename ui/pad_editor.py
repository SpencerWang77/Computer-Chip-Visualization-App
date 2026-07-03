from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout, QWidget)


class PadEditor(QWidget):
    """Edit panel for a single pad: name, net name and bonding target."""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pad = None
        self.original_data = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Read-only fields
        self.pad_id_label = QLabel("Pad ID: -")
        self.pad_id_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.pad_id_label)

        self.coord_label = QLabel("Coordinates: -")
        layout.addWidget(self.coord_label)

        self.size_label = QLabel("Size: -")
        layout.addWidget(self.size_label)

        # Editable fields
        edit_style = "border: 2px solid #bdc3c7; border-radius: 4px; padding: 5px;"

        layout.addWidget(QLabel("Pad Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(edit_style)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Net Name:"))
        self.net_edit = QLineEdit()
        self.net_edit.setStyleSheet(edit_style)
        layout.addWidget(self.net_edit)

        layout.addWidget(QLabel("Bonding (e.g. LF.12, VSS_ring, Not Bond):"))
        self.bonding_edit = QLineEdit()
        self.bonding_edit.setStyleSheet(edit_style)
        layout.addWidget(self.bonding_edit)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Revert")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 8px 16px;")
        self.cancel_btn.clicked.connect(self.cancel_changes)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 16px;")
        self.save_btn.clicked.connect(self.save_changes)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def load_pad(self, pad):
        self.current_pad = pad
        self.original_data = {
            'pad_name': pad.pad_name,
            'net_name': pad.net_name,
            'bonding': pad.bonding,
        }

        self.pad_id_label.setText(f"Pad ID: {pad.pad_id}")
        self.coord_label.setText(f"Coordinates: ({pad.x_coord:.4f}, {pad.y_coord:.4f}) µm")
        self.size_label.setText(f"Size: {pad.x_open:.2f} × {pad.y_open:.2f} µm")

        self.name_edit.setText(pad.pad_name)
        self.net_edit.setText(pad.net_name)
        self.bonding_edit.setText(pad.bonding)

    def cancel_changes(self):
        if self.current_pad and self.original_data:
            self.name_edit.setText(self.original_data['pad_name'])
            self.net_edit.setText(self.original_data['net_name'])
            self.bonding_edit.setText(self.original_data['bonding'])

    def save_changes(self):
        if not self.current_pad:
            return
        self.current_pad.update_info(
            pad_name=self.name_edit.text(),
            net_name=self.net_edit.text(),
            bonding=self.bonding_edit.text(),
        )
        QMessageBox.information(self, "Saved",
                                f"Changes to pad {self.current_pad.pad_id} saved.")
        self.data_changed.emit()
