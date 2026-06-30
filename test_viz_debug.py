import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from data_handlers import ExcelHandler
from ui import VisualizationWindow


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle("测试可视化窗口")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("准备加载数据...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        test_btn = QPushButton("测试打开可视化窗口")
        test_btn.clicked.connect(self.open_visualization)
        layout.addWidget(test_btn)
        
    def load_data(self):
        try:
            handler = ExcelHandler()
            excel_file = "封装连线示意.xlsx"
            
            if os.path.exists(excel_file):
                if handler.read_excel(excel_file):
                    self.pads = handler.get_pads()
                    self.status_label.setText(f"成功加载 {len(self.pads)} 个pad，点击按钮测试可视化")
                else:
                    self.status_label.setText("读取Excel文件失败")
                    self.pads = []
            else:
                self.status_label.setText("找不到测试文件")
                self.pads = []
        except Exception as e:
            self.status_label.setText(f"加载出错: {e}")
            self.pads = []
    
    def open_visualization(self):
        print("Opening visualization window...")
        if hasattr(self, 'pads') and self.pads:
            print(f"Creating VisualizationWindow with {len(self.pads)} pads")
            try:
                viz_window = VisualizationWindow(self.pads)
                print("VisualizationWindow created successfully")
                viz_window.show()
                print("VisualizationWindow.show() called successfully")
            except Exception as e:
                print(f"Error creating/showing visualization window: {e}")
        else:
            print("No pads available")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    test_window = TestWindow()
    test_window.show()
    
    sys.exit(app.exec_())
