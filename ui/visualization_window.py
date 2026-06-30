from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from ui.chip_visualization import ChipScene, ChipVisualizationView, PadInfoPanel
from models import Pad


class VisualizationWindow(QMainWindow):
    def __init__(self, pads: list, parent=None):
        super().__init__(parent)
        self.pads = pads
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("芯片Pad可视化")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("芯片Pad布局可视化")
        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        
        back_button = QPushButton("返回")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        back_button.clicked.connect(self.close)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        
        main_layout.addLayout(header_layout)
        
        content_splitter = QSplitter(Qt.Horizontal)
        
        self.scene = ChipScene()
        self.scene.set_pads(self.pads)
        self.scene.pad_clicked.connect(self.on_pad_clicked)
        
        self.view = ChipVisualizationView(self.scene)
        
        self.info_panel = PadInfoPanel()
        self.info_panel.setFixedWidth(300)
        
        content_splitter.addWidget(self.view)
        content_splitter.addWidget(self.info_panel)
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(content_splitter)
        
        # 自动缩放以适应所有内容
        self.auto_fit_view()
        
        # 状态栏 - 固定在底部，不占用太多空间
        self.status_label = QLabel(f"共加载 {len(self.pads)} 个Pad | 操作说明: 滚轮缩放，拖动移动，点击Pad查看详情")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                color: #7f8c8d;
                padding: 8px;
                border-radius: 5px;
                font-size: 11px;
                min-height: 35px;
                max-height: 35px;
            }
        """)
        main_layout.addWidget(self.status_label, 0)  # 设置stretch为0，不自动扩展
        
        self.apply_modern_style()
    
    def on_pad_clicked(self, pad: Pad):
        self.info_panel.show_pad_info(pad)
    
    def auto_fit_view(self):
        # 获取场景矩形
        scene_rect = self.scene.sceneRect()
        
        if scene_rect.isEmpty():
            return
        
        # 添加一些边距
        margin = 20
        padded_rect = scene_rect.adjusted(-margin, -margin, margin, margin)
        
        # 适应视图
        self.view.fitInView(padded_rect, Qt.KeepAspectRatio)
        
        # 手动进行放大，确保文字可见
        self.view.scale(1.5, 1.5)
    
    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
        """)
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        self.setPalette(palette)
