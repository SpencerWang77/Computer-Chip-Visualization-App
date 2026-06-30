import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from data_handlers import ExcelHandler
from ui import VisualizationWindow

class SimpleTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("简化测试")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.label = QLabel("准备测试")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        self.btn1 = QPushButton("1. 加载数据")
        self.btn1.clicked.connect(self.load_data)
        layout.addWidget(self.btn1)
        
        self.btn2 = QPushButton("2. 测试创建可视化窗口")
        self.btn2.clicked.connect(self.test_create_viz)
        self.btn2.setEnabled(False)
        layout.addWidget(self.btn2)
        
        self.pads = []
        
    def load_data(self):
        try:
            handler = ExcelHandler()
            excel_file = "封装连线示意.xlsx"
            
            if os.path.exists(excel_file):
                if handler.read_excel(excel_file):
                    self.pads = handler.get_pads()
                    self.label.setText(f"✓ 成功加载 {len(self.pads)} 个pads")
                    self.btn2.setEnabled(True)
                    self.btn1.setEnabled(False)
                else:
                    self.label.setText("✗ 读取Excel文件失败")
            else:
                self.label.setText("✗ 找不到测试文件")
        except Exception as e:
            self.label.setText(f"✗ 加载出错: {e}")
    
    def test_create_viz(self):
        self.label.setText("正在创建可视化窗口...")
        try:
            print(f"Creating VisualizationWindow with {len(self.pads)} pads")
            viz_window = VisualizationWindow(self.pads)
            print("VisualizationWindow created")
            viz_window.show()
            print("VisualizationWindow.show() called")
            self.label.setText(f"✓ 可视化窗口已打开 | 共 {len(self.pads)} 个pads")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.label.setText(f"✗ 创建失败: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    test = SimpleTest()
    test.show()
    
    sys.exit(app.exec_())
