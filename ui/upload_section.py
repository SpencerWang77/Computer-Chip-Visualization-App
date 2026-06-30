from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, 
                             QPushButton, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt


class UploadSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("导入数据", parent)
        self.file_label = None
        self.upload_btn = None
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
        
        self.file_label = QLabel("未选择文件")
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
        
        self.upload_btn = QPushButton("选择 Excel 文件")
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
    
    def set_file_selected(self, file_name: str):
        self.file_label.setText("已选择: " + file_name)
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
