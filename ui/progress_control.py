from PyQt5.QtWidgets import QPushButton, QLabel
from PyQt5.QtCore import Qt


class ProgressControl:
    def __init__(self):
        self.start_btn = None
        self.status_label = None
    
    def create_status_label(self):
        self.status_label = QLabel("等待选择文件")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                color: #7f8c8d;
                font-size: 13px;
            }
        """)
        return self.status_label
    
    def create_start_button(self):
        self.start_btn = QPushButton("开始可视化")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 30px;
                font-size: 16px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #bdc3c7;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a7d;
            }
        """)
        return self.start_btn
    
    def set_loading_status(self):
        if self.status_label:
            self.status_label.setText("正在读取Excel文件...")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 8px;
                    padding: 15px;
                    color: #856404;
                    font-size: 13px;
                }
            """)
    
    def set_success_status(self):
        if self.status_label:
            self.status_label.setText("文件读取完成，可以开始可视化")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    padding: 15px;
                    color: #155724;
                    font-size: 13px;
                }
            """)
    
    def enable_start_button(self):
        if self.start_btn:
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 30px;
                    font-size: 16px;
                    font-weight: bold;
                    min-height: 45px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
    
    def disable_start_button(self):
        if self.start_btn:
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 30px;
                    font-size: 16px;
                    font-weight: bold;
                    min-height: 45px;
                }
                QPushButton:disabled {
                    background-color: #95a5a6;
                    color: #bdc3c7;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:pressed {
                    background-color: #6c7a7d;
                }
            """)
    
    def show_start_button(self):
        if self.start_btn:
            self.start_btn.show()
    
    def hide_start_button(self):
        if self.start_btn:
            self.start_btn.hide()
    
    def show_status_label(self):
        if self.status_label:
            self.status_label.show()
    
    def hide_status_label(self):
        if self.status_label:
            self.status_label.hide()