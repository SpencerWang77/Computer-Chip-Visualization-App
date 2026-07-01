from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, 
                              QPushButton, QSpacerItem, QSizePolicy, 
                              QLineEdit, QHBoxLayout, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator


class UploadSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("导入数据", parent)
        self.file_label = None
        self.upload_btn = None
        
        # 框架参数
        self.die_width_input = None
        self.die_height_input = None
        self.lf_count_input = None
        
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
        
        # 框架设置区域
        self._add_frame_settings(layout)
    
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
    
    def _add_frame_settings(self, parent_layout):
        """添加框架设置输入区域"""
        # 框架设置标题
        frame_title = QLabel("框架设置")
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
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        # Die宽度输入
        self.die_width_input = QLineEdit()
        self.die_width_input.setPlaceholderText("例如: 5000")
        self.die_width_input.setText("3475.8")  # 默认值
        self.die_width_input.setValidator(QDoubleValidator(0.1, 100000.0, 2))
        self.die_width_input.setStyleSheet("""
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
        """)
        form_layout.addRow("Die 宽度 (μm):", self.die_width_input)
        
        # Die高度输入
        self.die_height_input = QLineEdit()
        self.die_height_input.setPlaceholderText("例如: 5000")
        self.die_height_input.setText("3105")  # 默认值
        self.die_height_input.setValidator(QDoubleValidator(0.1, 100000.0, 2))
        self.die_height_input.setStyleSheet(self.die_width_input.styleSheet())
        form_layout.addRow("Die 高度 (μm):", self.die_height_input)
        
        # Pin Count输入
        self.lf_count_input = QLineEdit()
        self.lf_count_input.setPlaceholderText("例如: 16")
        self.lf_count_input.setText("130")  # 默认值
        self.lf_count_input.setValidator(QIntValidator(4, 1000))
        self.lf_count_input.setStyleSheet(self.die_width_input.styleSheet())
        form_layout.addRow("Pin Count:", self.lf_count_input)
        
        # 提示标签
        info_label = QLabel("* Pin Count ÷ 4 = 每边引脚数")
        info_label.setAlignment(Qt.AlignCenter)
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
    
    def get_frame_parameters(self):
        """获取框架参数"""
        try:
            die_width = float(self.die_width_input.text()) if self.die_width_input.text() else None
            die_height = float(self.die_height_input.text()) if self.die_height_input.text() else None
            pin_count = int(self.lf_count_input.text()) if self.lf_count_input.text() else None
            
            return {
                'die_width': die_width,
                'die_height': die_height,
                'lf_count': pin_count  # 保持内部变量名兼容性
            }
        except ValueError:
            return None
