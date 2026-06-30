from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class FormatDescription(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("文件格式说明", parent)
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
支持的文件格式：
• Excel 文件 (.xlsx, .xls)
• 必须包含以下工作表：
  - connect: Pad连接信息 (Die Pad No, Pad name, X-coord, Y-coord, X open, Y open, Net Name, Bonding)
  - ring: Ring配置信息
  - ref-fig: 参考图表信息

数据格式要求：
• 第一行为字段标题
• 第二行为单位说明或备注
• 第三行开始为实际数据
• 坐标数据为数值型
        """)
        format_text.setStyleSheet("color: #34495e; font-size: 11px; line-height: 1.6;")
        format_text.setAlignment(Qt.AlignLeft)
        layout.addWidget(format_text)
