import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                             QLabel, QMessageBox, QPushButton, QSplitter,
                             QVBoxLayout, QWidget)

from data_handlers import ExcelExporter
from ui.chip_visualization import ChipScene, ChipVisualizationView
from ui.pad_editor import PadEditor


class EditorWindow(QWidget):
    """Editor page: bonding diagram on the left, pad editor on the right.

    This is a page inside the single application window; it emits
    `back_requested` when the user wants to return to the upload page.
    """

    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.pads = []
        self.source_file = None
        self.setAutoFillBackground(True)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Back to Upload")
        back_btn.setToolTip("Return to the upload page")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        back_btn.clicked.connect(self.back_requested.emit)

        title_label = QLabel("Chip Pad Editor")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        self.wires_checkbox = QCheckBox("Show bond wires")
        self.wires_checkbox.setChecked(True)
        self.wires_checkbox.toggled.connect(self._on_wires_toggled)

        rotate_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        rotate_ccw_btn = QPushButton("Rotate 90° CCW")
        rotate_ccw_btn.setToolTip("Rotate the die and its pads 90° counterclockwise")
        rotate_ccw_btn.setStyleSheet(rotate_style)
        rotate_ccw_btn.clicked.connect(lambda: self._rotate_die(90))

        rotate_cw_btn = QPushButton("Rotate 90° CW")
        rotate_cw_btn.setToolTip("Rotate the die and its pads 90° clockwise")
        rotate_cw_btn.setStyleSheet(rotate_style)
        rotate_cw_btn.clicked.connect(lambda: self._rotate_die(-90))

        # Choose what each pad displays.
        display_label = QLabel("Show on pad:")
        display_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.display_combo = QComboBox()
        self.display_combo.setToolTip("Choose what each pad shows in the diagram")
        # (label, mode key)
        for text, mode in [("Original pad number", 'soc'),
                           ("Position number (after rotation)", 'position'),
                           ("Bond target (LF no. / V·E·N·O·U)", 'bond')]:
            self.display_combo.addItem(text, mode)
        self.display_combo.currentIndexChanged.connect(self._on_display_mode_changed)

        header_layout.addWidget(back_btn)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.wires_checkbox)
        header_layout.addWidget(rotate_ccw_btn)
        header_layout.addWidget(rotate_cw_btn)
        header_layout.addWidget(display_label)
        header_layout.addWidget(self.display_combo)
        main_layout.addLayout(header_layout)

        # Content: visualization | editor
        content_splitter = QSplitter(Qt.Horizontal)

        self.scene = ChipScene()
        self.view = ChipVisualizationView(self.scene)
        content_splitter.addWidget(self.view)

        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)

        edit_title = QLabel("Pad Properties")
        edit_title.setFont(QFont("Arial", 14, QFont.Bold))
        edit_title.setStyleSheet("color: #2c3e50; padding: 10px;")
        edit_title.setAlignment(Qt.AlignCenter)
        edit_layout.addWidget(edit_title)

        self.editor = PadEditor()
        self.editor.data_changed.connect(self._on_pad_edited)
        edit_layout.addWidget(self.editor)

        # Export button + option
        export_layout = QHBoxLayout()
        self.renumber_checkbox = QCheckBox("Use position number as pad No.")
        self.renumber_checkbox.setToolTip(
            "Export each pad numbered by its position around the die\n"
            "(the same numbering as the 'Position number' display mode)")
        export_layout.addWidget(self.renumber_checkbox)
        export_layout.addStretch()
        self.export_btn = QPushButton("Export Modified Excel")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_modified_excel)
        export_layout.addWidget(self.export_btn)
        edit_layout.addLayout(export_layout)

        # Legend
        legend_title = QLabel("Legend:")
        legend_title.setFont(QFont("Arial", 12, QFont.Bold))
        legend_title.setStyleSheet("color: #2c3e50; padding: 5px 10px 0 10px;")
        edit_layout.addWidget(legend_title)

        legend_text = QLabel(
            "Pad colors (by bonding target):\n"
            "  Black — Not Bond (no wire)\n"
            "  Dark blue — VSS ring / E-PAD ring\n"
            "  Light colors — bonded to a lead frame pin\n"
            "  Dark gray — die-to-die (SOC/PSRAM/DDRA/DDRB/ROM)\n"
            "  Dark red — unrecognized bonding value\n"
            "  Orange border — selected pad\n"
            "Bond wires: gray = to a lead frame pin, blue = to the VSS ring.\n"
            "Lead frame pins are drawn solid black and labeled LF.<n>.\n"
            "\n"
            "\"Show on pad\" = Bond target codes:\n"
            "  <number> — lead frame pin number it bonds to\n"
            "  V — VSS ring        E — E-pad\n"
            "  N — Not bonded      O — other die\n"
            "  U — undefined / unrecognized"
        )
        legend_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                margin: 0 10px;
                color: #2c3e50;
                font-size: 11px;
            }
        """)
        legend_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        edit_layout.addWidget(legend_text)

        content_splitter.addWidget(edit_widget)
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(content_splitter, 1)

        # Status bar
        self.status_label = QLabel("Load an Excel file to start editing")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px 15px;
                font-size: 11px;
            }
        """)
        main_layout.addWidget(self.status_label)

        self.scene.pad_clicked.connect(self._on_pad_selected)
        self._apply_style()

    # --- data -----------------------------------------------------------

    def set_data(self, pads, frame_params=None, source_file=None):
        """Show the given pads (used by the upload page for each new file)."""
        self.pads = pads
        self.source_file = source_file

        # Reset view options for a fresh file (without triggering redraws).
        self.scene.reset_view()
        controls = (self.display_combo, self.wires_checkbox, self.renumber_checkbox)
        for widget in controls:
            widget.blockSignals(True)
        self.display_combo.setCurrentIndex(0)
        self.wires_checkbox.setChecked(True)
        self.renumber_checkbox.setChecked(False)
        for widget in controls:
            widget.blockSignals(False)
        self.editor.clear()

        self.scene.set_pads(pads, frame_params)
        self.view.fit_in_view()
        self.export_btn.setEnabled(bool(pads))
        self.status_label.setText(
            f"Loaded {len(pads)} pads | Die drawn with actual proportion | Click a pad to edit its name, "
            f"net name or bonding type.")

    # --- interaction ------------------------------------------------------

    def _on_wires_toggled(self, checked):
        self.scene.set_wires_visible(checked)

    def _on_pad_selected(self, pad):
        self.editor.load_pad(pad, self.scene.rotated_geometry(pad))

    def _rotate_die(self, degrees):
        """Rotate the die 90° (positive = counterclockwise) and refit the view."""
        self.scene.rotate_die(degrees)
        self._restore_selection()
        self.view.fit_in_view()

    def _on_display_mode_changed(self, _index):
        self.scene.set_display_mode(self.display_combo.currentData())
        self._restore_selection()

    def _restore_selection(self):
        """Re-select and re-highlight the current pad after a redraw, and
        refresh its after-rotation geometry."""
        selected = self.editor.current_pad
        if selected is not None:
            self.editor.update_rotated(self.scene.rotated_geometry(selected))
            item = self.scene.pad_items.get(selected.pad_id)
            if item is not None:
                item.setSelected(True)
                self.scene._highlight_wire(selected.pad_id)

    def _on_pad_edited(self):
        """Redraw so colors and wires reflect the new bonding value."""
        edited_pad = self.editor.current_pad
        self.scene.refresh()
        if edited_pad is not None:
            item = self.scene.pad_items.get(edited_pad.pad_id)
            if item is not None:
                item.setSelected(True)
                self.scene._highlight_wire(edited_pad.pad_id)

    # --- export ------------------------------------------------------------

    def export_modified_excel(self):
        try:
            default_dir = os.path.join(os.getcwd(), ExcelExporter.DEFAULT_EXPORT_DIR)
            os.makedirs(default_dir, exist_ok=True)
            exporter = ExcelExporter(source_file=self.source_file)

            from datetime import datetime
            suggested = os.path.join(
                default_dir,
                f"modified_pads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

            output_path, _ = QFileDialog.getSaveFileName(
                self, "Export Modified Excel", suggested,
                "Excel files (*.xlsx);;All files (*.*)")
            if not output_path:
                return

            # Bake the current rotation into the exported coordinates/sizes,
            # optionally renumbering pads by their position.
            export_pads = self.scene.pads_with_rotation_applied(
                renumber_by_position=self.renumber_checkbox.isChecked())
            success, saved_path = exporter.export_modified_data(export_pads, output_path)
            if not success:
                QMessageBox.warning(self, "Export Failed", "Could not export the Excel file.")
                return

            summary = exporter.get_export_summary(export_pads)
            QMessageBox.information(
                self, "Export Successful",
                f"Saved to: {saved_path}\n"
                f"Modified pads: {summary['modified_pads']}/{summary['total_pads']}\n"
                f"Export time: {summary['export_time']}\n\n"
                f"The original Excel file was not modified.")
            self.status_label.setText(
                f"Exported {summary['modified_pads']}/{summary['total_pads']} "
                f"modified pads to {saved_path}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Export Error", f"Error during export: {e}")

    # --- style ------------------------------------------------------------

    def _apply_style(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        self.setPalette(palette)
