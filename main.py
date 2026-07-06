"""Chip bonding visualization — entry point.

Opens the upload window where the user picks an Excel bonding file and
sets the package parameters, then launches the pad editor.
"""

import os
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                             QScrollArea, QSizePolicy, QSpacerItem,
                             QStackedWidget, QVBoxLayout, QWidget)

from data_handlers import ExcelHandler
from ui import EditorWindow, FormatDescription, ProgressControl, UploadSection


class ChipVisApp(QMainWindow):
    """Single application window that switches between an upload page and the
    editor page (so there is only ever one window on screen)."""

    def __init__(self):
        super().__init__()
        self.excel_handler = ExcelHandler()
        self.current_file = None
        self.progress_control = ProgressControl()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chip Bonding Visualization")
        self.resize(1280, 860)  # fallback size if the user un-maximizes
        self.setWindowState(self.windowState() | Qt.WindowMaximized)

        # One central stack: page 0 = upload, page 1 = editor.
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.stack.addWidget(self._build_upload_page())

        self.editor_page = EditorWindow()
        self.editor_page.back_requested.connect(self._show_upload_page)
        self.stack.addWidget(self.editor_page)

    def _build_upload_page(self) -> QWidget:
        # Scrollable container so the Start button stays reachable on short windows.
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        central_widget = QWidget()
        scroll_area.setWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel("Chip Bonding Visualization")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)

        self.upload_section = UploadSection()
        self.upload_section.get_upload_button().clicked.connect(self.open_file_dialog)
        main_layout.addWidget(self.upload_section)

        main_layout.addWidget(FormatDescription())

        status_label = self.progress_control.create_status_label()
        self.progress_control.hide_status_label()
        main_layout.addWidget(status_label)

        start_button = self.progress_control.create_start_button()
        start_button.clicked.connect(self.start_visualization)
        self.progress_control.hide_start_button()
        main_layout.addWidget(start_button, 0, Qt.AlignCenter)

        main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        return scroll_area

    def _show_upload_page(self):
        self.stack.setCurrentIndex(0)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "",
            "Excel files (*.xlsx *.xls);;All files (*.*)")
        if not file_path:
            return

        self.current_file = file_path
        self.upload_section.set_file_selected(os.path.basename(file_path))
        self.progress_control.show_start_button()
        self.progress_control.show_status_label()
        self.read_excel_file()

    def read_excel_file(self):
        self.progress_control.set_loading_status()
        self.progress_control.disable_start_button()

        if self.excel_handler.read_excel(self.current_file):
            dies = self.excel_handler.get_dies()
            print(f"Loaded {len(dies)} die(s) from {self.current_file}: "
                  f"{', '.join(d.name for d in dies)}")

            # Pre-fill the pin count from the data; the user can override it.
            self.upload_section.set_pin_count(self.excel_handler.suggest_pin_count())

            self.progress_control.set_success_status()
            self.progress_control.enable_start_button()
        else:
            self.progress_control.set_error_status()

    def start_visualization(self):
        if not self.current_file:
            return

        dies = self.excel_handler.get_dies()
        if not dies:
            self.progress_control.set_error_status("No dies found in the file")
            return

        frame_params = self.upload_section.get_frame_parameters()

        self.editor_page.set_data(dies, frame_params,
                                  source_file=self.current_file)
        self.stack.setCurrentIndex(1)
        # Fit once the editor page has taken its final size.
        QTimer.singleShot(0, self.editor_page.view.fit_in_view)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(244, 247, 250))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.Button, QColor(236, 240, 241))
    palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))
    palette.setColor(QPalette.Highlight, QColor(41, 128, 185))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = ChipVisApp()
    window.showMaximized()  # always open filling the screen
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
