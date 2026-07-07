import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDoubleValidator, QFont, QPalette
from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                             QFileDialog, QFormLayout, QFrame, QHBoxLayout,
                             QLabel, QLineEdit, QListWidget, QMenu, QMessageBox,
                             QPushButton, QScrollArea, QSplitter, QVBoxLayout,
                             QWidget, QWidgetAction)

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
        self.dies = []
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

        self.padnames_checkbox = QCheckBox("Show pad names")
        self.padnames_checkbox.setChecked(False)
        self.padnames_checkbox.toggled.connect(self._on_padnames_toggled)

        # Die stacking priority (drag to reorder; higher = on top).
        priority_btn = self._build_priority_control()

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

        header_layout.setSpacing(12)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.wires_checkbox)
        header_layout.addWidget(self.padnames_checkbox)
        header_layout.addWidget(priority_btn)
        header_layout.addSpacing(8)
        header_layout.addWidget(display_label)
        header_layout.addWidget(self.display_combo)
        header_layout.addSpacing(8)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)

        # Content: visualization | editor
        content_splitter = QSplitter(Qt.Horizontal)

        self.scene = ChipScene()
        self.view = ChipVisualizationView(self.scene)
        content_splitter.addWidget(self.view)

        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        edit_layout.setContentsMargins(14, 12, 14, 12)
        edit_layout.setSpacing(12)

        edit_title = QLabel("Pad Properties")
        edit_title.setFont(QFont("Arial", 14, QFont.Bold))
        edit_title.setStyleSheet("color: #2c3e50;")
        edit_title.setAlignment(Qt.AlignCenter)
        edit_layout.addWidget(edit_title)

        self.editor = PadEditor()
        self.editor.data_changed.connect(self._on_pad_edited)
        edit_layout.addWidget(self.editor)

        edit_layout.addWidget(self._divider())

        # Die placement: numeric alternative to dragging / handle rotation.
        place_title = QLabel("Die placement")
        place_title.setFont(QFont("Arial", 12, QFont.Bold))
        place_title.setStyleSheet("color: #2c3e50;")
        edit_layout.addWidget(place_title)

        # Which die the placement controls act on (click a die on the canvas
        # also selects it here).
        die_row = QHBoxLayout()
        die_row.setSpacing(8)
        die_row.addWidget(QLabel("Die:"))
        self.die_combo = QComboBox()
        self.die_combo.setToolTip("The die that the placement controls act on")
        self.die_combo.currentIndexChanged.connect(self._on_die_combo_changed)
        die_row.addWidget(self.die_combo, 1)

        small_rot_style = (
            "QPushButton { background-color: #3498db; color: white; border: none;"
            " border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background-color: #2980b9; }")
        rot_ccw_btn = QPushButton("↺ 90°")
        rot_ccw_btn.setToolTip("Rotate the selected die 90° counterclockwise")
        rot_ccw_btn.setStyleSheet(small_rot_style)
        rot_ccw_btn.clicked.connect(lambda: self._rotate_die(90))
        rot_cw_btn = QPushButton("↻ 90°")
        rot_cw_btn.setToolTip("Rotate the selected die 90° clockwise")
        rot_cw_btn.setStyleSheet(small_rot_style)
        rot_cw_btn.clicked.connect(lambda: self._rotate_die(-90))
        die_row.addWidget(rot_ccw_btn)
        die_row.addWidget(rot_cw_btn)
        edit_layout.addLayout(die_row)

        field_style = "border: 1px solid #bdc3c7; border-radius: 4px; padding: 5px;"
        place_form = QFormLayout()
        place_form.setSpacing(8)
        place_form.setContentsMargins(0, 0, 0, 0)
        place_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.die_x_edit = QLineEdit()
        self.die_y_edit = QLineEdit()
        self.die_rot_edit = QLineEdit()
        for label_text, edit in (("Center X (µm):", self.die_x_edit),
                                 ("Center Y (µm):", self.die_y_edit),
                                 ("Rotation (°):", self.die_rot_edit)):
            edit.setValidator(QDoubleValidator(-1e7, 1e7, 4))
            edit.setStyleSheet(field_style)
            edit.returnPressed.connect(self._apply_die_placement)
            place_form.addRow(label_text, edit)
        edit_layout.addLayout(place_form)

        place_buttons = QHBoxLayout()
        place_buttons.setSpacing(8)
        apply_btn = QPushButton("Apply")
        apply_btn.setToolTip("Move/rotate the die to these values")
        apply_btn.setStyleSheet(self._button_style("#3498db", "#2980b9"))
        apply_btn.clicked.connect(self._apply_die_placement)
        reset_btn = QPushButton("Reset")
        reset_btn.setToolTip("Recenter the die and clear its rotation")
        reset_btn.setStyleSheet(self._button_style("#95a5a6", "#7f8c8d"))
        reset_btn.clicked.connect(self._reset_die_placement)
        place_buttons.addWidget(apply_btn)
        place_buttons.addWidget(reset_btn)
        edit_layout.addLayout(place_buttons)

        edit_layout.addWidget(self._divider())

        # VSS ring size (editable live).
        ring_title = QLabel("VSS ring size")
        ring_title.setFont(QFont("Arial", 12, QFont.Bold))
        ring_title.setStyleSheet("color: #2c3e50;")
        edit_layout.addWidget(ring_title)

        ring_row = QHBoxLayout()
        ring_row.setSpacing(6)
        self.ring_w_edit = QLineEdit()
        self.ring_h_edit = QLineEdit()
        for edit in (self.ring_w_edit, self.ring_h_edit):
            edit.setValidator(QDoubleValidator(1.0, 1e7, 2))
            edit.setStyleSheet(field_style)
            edit.returnPressed.connect(self._apply_ring_size)
        times = QLabel("×")
        times.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        ring_apply = QPushButton("Apply")
        ring_apply.setToolTip("Resize the VSS ring (µm); dies stay in place")
        ring_apply.setStyleSheet(self._button_style("#3498db", "#2980b9"))
        ring_apply.clicked.connect(self._apply_ring_size)
        ring_row.addWidget(QLabel("W"))
        ring_row.addWidget(self.ring_w_edit)
        ring_row.addWidget(times)
        ring_row.addWidget(QLabel("H"))
        ring_row.addWidget(self.ring_h_edit)
        ring_row.addWidget(ring_apply)
        edit_layout.addLayout(ring_row)

        edit_layout.addWidget(self._divider())

        # Export section
        export_title = QLabel("Export")
        export_title.setFont(QFont("Arial", 12, QFont.Bold))
        export_title.setStyleSheet("color: #2c3e50;")
        edit_layout.addWidget(export_title)

        self.renumber_checkbox = QCheckBox("Use position number as pad No.")
        self.renumber_checkbox.setToolTip(
            "Export each pad numbered by its position around the die\n"
            "(the same numbering as the 'Position number' display mode)")
        edit_layout.addWidget(self.renumber_checkbox)

        self.export_btn = QPushButton("Export Modified Excel")
        self.export_btn.setStyleSheet(self._button_style("#27ae60", "#229954", height=38))
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_modified_excel)
        edit_layout.addWidget(self.export_btn)

        edit_layout.addWidget(self._divider())

        # Legend
        legend_title = QLabel("Legend")
        legend_title.setFont(QFont("Arial", 12, QFont.Bold))
        legend_title.setStyleSheet("color: #2c3e50;")
        edit_layout.addWidget(legend_title)

        legend_text = QLabel(
            "Pad colors (by bonding target):\n"
            "  Black — Not Bond (no wire)\n"
            "  Dark blue — VSS ring / E-PAD ring\n"
            "  Light colors — bonded to a lead frame pin\n"
            "  Dark gray — die-to-die (SOC/PSRAM/DDRA/DDRB/ROM)\n"
            "  Dark red — unrecognized bonding value\n"
            "  Orange border — selected pad / selected die\n"
            "Bond wires: gray = lead frame pin, blue = VSS ring,\n"
            "  purple = die-to-die (pad → pad on another die).\n"
            "Lead frame pins are drawn solid black and labeled LF.<n>.\n"
            "The ring and pins are fixed; each die moves/rotates on its own\n"
            "(click a die to select it). Dies start arranged side by side.\n"
            "\"Show pad names\" labels each pad; \"Priority\" sets which die is\n"
            "drawn on top when dies overlap (drag to reorder).\n"
            "Ring (0,0): the axes at the ring's bottom-left corner are the\n"
            "origin of the shared ring coordinate system (shown per pad).\n"
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
                color: #2c3e50;
                font-size: 11px;
            }
        """)
        legend_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        legend_text.setWordWrap(True)
        edit_layout.addWidget(legend_text)
        edit_layout.addStretch()

        # Wrap the right panel so it scrolls when taller than the window.
        edit_scroll = QScrollArea()
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setFrameShape(QScrollArea.NoFrame)
        edit_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit_scroll.setWidget(edit_widget)

        content_splitter.addWidget(edit_scroll)
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setSizes([1100, 380])
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
        self.scene.die_transform_changed.connect(self._on_die_transform_changed)
        self.scene.die_selected.connect(self._on_scene_die_selected)
        self._apply_style()

    def _build_priority_control(self):
        """A 'Priority' button opening a drag-reorderable list of dies; the
        top item is drawn on top of overlapping dies."""
        self.priority_list = QListWidget()
        self.priority_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.priority_list.setToolTip("Drag to reorder — top die is drawn on top")
        self.priority_list.setFixedWidth(150)
        self.priority_list.model().rowsMoved.connect(self._on_priority_reordered)

        container = QWidget()
        box = QVBoxLayout(container)
        box.setContentsMargins(8, 8, 8, 8)
        box.setSpacing(4)
        hint = QLabel("Die priority (drag to reorder;\ntop = drawn on top):")
        hint.setStyleSheet("color: #2c3e50; font-size: 11px;")
        box.addWidget(hint)
        box.addWidget(self.priority_list)

        menu = QMenu(self)
        action = QWidgetAction(menu)
        action.setDefaultWidget(container)
        menu.addAction(action)

        btn = QPushButton("Priority ▾")
        btn.setToolTip("Set which die is drawn on top when dies overlap")
        btn.setStyleSheet(
            "QPushButton { background-color: #ecf0f1; color: #2c3e50;"
            " border: 1px solid #bdc3c7; border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background-color: #dfe4ea; }")
        btn.setMenu(menu)
        return btn

    # --- data -----------------------------------------------------------

    def set_data(self, dies, frame_params=None, source_file=None):
        """Show the given dies (used by the upload page for each new file)."""
        self.dies = dies
        self.source_file = source_file

        # Reset view options for a fresh file (without triggering redraws).
        self.scene.reset_view()
        controls = (self.display_combo, self.wires_checkbox, self.padnames_checkbox,
                    self.renumber_checkbox, self.die_combo, self.priority_list)
        for widget in controls:
            widget.blockSignals(True)
        self.display_combo.setCurrentIndex(0)
        self.wires_checkbox.setChecked(True)
        self.padnames_checkbox.setChecked(False)
        self.renumber_checkbox.setChecked(False)
        self.die_combo.clear()
        self.die_combo.addItems([d.name for d in dies])
        self.priority_list.clear()
        self.priority_list.addItems([d.name for d in dies])
        for widget in controls:
            widget.blockSignals(False)
        self.editor.clear()

        self.scene.set_dies(dies, frame_params)
        self.view.fit_in_view()
        self._sync_die_fields()
        self._sync_ring_fields()
        self.export_btn.setEnabled(bool(dies))
        total_pads = sum(len(d.pads) for d in dies)
        die_word = "die" if len(dies) == 1 else "dies"
        self.status_label.setText(
            f"Loaded {len(dies)} {die_word} ({total_pads} pads) | Click a die to "
            f"select it, drag to move, drag the handle to rotate | Click a pad to edit.")

    # --- interaction ------------------------------------------------------

    def _current_die(self):
        idx = self.scene.selected_die()
        return idx if idx is not None else 0

    def _on_wires_toggled(self, checked):
        self.scene.set_wires_visible(checked)

    def _on_padnames_toggled(self, checked):
        self.scene.set_pad_names_visible(checked)

    def _on_priority_reordered(self, *args):
        order = [self.priority_list.item(i).text()
                 for i in range(self.priority_list.count())]
        self.scene.set_die_priority(order)

    def _on_pad_selected(self, pad):
        self.editor.load_pad(pad, self.scene.die_name_of(pad),
                             self.scene.ring_coords(pad),
                             self.scene.rotated_geometry(pad))

    def _on_die_combo_changed(self, index):
        if index >= 0:
            self.scene.select_die(index)

    def _on_scene_die_selected(self, index):
        if self.die_combo.currentIndex() != index:
            self.die_combo.blockSignals(True)
            self.die_combo.setCurrentIndex(index)
            self.die_combo.blockSignals(False)
        self._sync_die_fields()

    def _rotate_die(self, degrees):
        """Rotate the selected die 90° (keeps its position)."""
        self.scene.rotate_die(self._current_die(), degrees)
        self._restore_selection()

    def _apply_die_placement(self):
        """Numeric alternative to hand drag/rotation, for the selected die."""
        try:
            x = float(self.die_x_edit.text())
            y = float(self.die_y_edit.text())
            rotation = float(self.die_rot_edit.text())
        except ValueError:
            return
        self.scene.set_die_transform(self._current_die(), x, y, rotation)
        self._restore_selection()

    def _reset_die_placement(self):
        self.scene.reset_die_transform(self._current_die())
        self._restore_selection()

    def _apply_ring_size(self):
        """Resize the VSS ring live from the panel fields."""
        try:
            w = float(self.ring_w_edit.text())
            h = float(self.ring_h_edit.text())
        except ValueError:
            return
        self.scene.set_ring_size(w, h)
        self._sync_ring_fields()
        self._restore_selection()

    def _sync_ring_fields(self):
        size = self.scene.ring_size()
        if size is not None:
            self.ring_w_edit.setText(f"{size[0]:.1f}")
            self.ring_h_edit.setText(f"{size[1]:.1f}")

    def _on_die_transform_changed(self, index, center_x, center_y, rotation):
        """Live sync while a die is dragged/rotated (by hand or numerically)."""
        if index == self._current_die():
            self.die_x_edit.setText(f"{center_x:.1f}")
            self.die_y_edit.setText(f"{center_y:.1f}")
            self.die_rot_edit.setText(f"{rotation:.1f}")
        selected = self.editor.current_pad
        if selected is not None:
            self.editor.update_rotated(self.scene.rotated_geometry(selected))
            self.editor.update_ring_coords(self.scene.ring_coords(selected))

    def _sync_die_fields(self):
        if not self.dies:
            return
        center_x, center_y, rotation = self.scene.die_transform(self._current_die())
        self.die_x_edit.setText(f"{center_x:.1f}")
        self.die_y_edit.setText(f"{center_y:.1f}")
        self.die_rot_edit.setText(f"{rotation:.1f}")

    def _on_display_mode_changed(self, _index):
        self.scene.set_display_mode(self.display_combo.currentData())
        self._restore_selection()

    def _restore_selection(self):
        """Re-select and re-highlight the current pad after a redraw, and
        refresh its transformed geometry and ring coordinates."""
        selected = self.editor.current_pad
        if selected is not None:
            self.editor.update_rotated(self.scene.rotated_geometry(selected))
            self.editor.update_ring_coords(self.scene.ring_coords(selected))
            item = self.scene.pad_items.get(selected.pad_id)
            if item is not None:
                item.setSelected(True)
                self.scene._highlight_wire(selected.pad_id)

    def _on_pad_edited(self):
        """Redraw so colors and wires reflect the new bonding value."""
        self.scene.refresh()
        self._restore_selection()

    # --- export ------------------------------------------------------------

    def export_modified_excel(self):
        try:
            exporter = ExcelExporter(source_file=self.source_file)

            from datetime import datetime
            suggested = os.path.join(
                os.path.expanduser("~"),
                f"modified_pads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

            output_path, _ = QFileDialog.getSaveFileName(
                self, "Export Modified Excel", suggested,
                "Excel files (*.xlsx);;All files (*.*)")
            if not output_path:
                return

            # One 'Die Netlist(<name>)' tab per die (die-local coordinates),
            # plus a 'Basic information' sheet recording the ring size and each
            # die's placement so the file reopens exactly where it left off.
            export_rows = self.scene.pads_for_export(
                renumber_by_position=self.renumber_checkbox.isChecked())
            metadata = self.scene.layout_metadata()
            success, saved_path = exporter.export_by_die(export_rows, output_path,
                                                         metadata)
            if not success:
                QMessageBox.warning(self, "Export Failed", "Could not export the Excel file.")
                return

            summary = exporter.get_export_summary([p for _, p in export_rows])
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

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #dfe4ea; background-color: #dfe4ea; max-height: 1px;")
        return line

    @staticmethod
    def _button_style(base, hover, height=30) -> str:
        return f"""
            QPushButton {{
                background-color: {base};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 7px 14px;
                font-weight: bold;
                min-height: {height}px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{ background-color: #b2bec3; }}
        """

    def _apply_style(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        self.setPalette(palette)
