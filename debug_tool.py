import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Tool")
        self.setGeometry(100, 100, 300, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Test 1: Check file existence
        test1_label = QLabel("Test 1: File check")
        test1_result = self.test_file_existence()
        test1_label.setText(f"Test 1: {test1_result}")
        layout.addWidget(test1_label)
        
        # Test 2: Import modules
        test2_label = QLabel("Test 2: Module imports")
        test2_result = self.test_module_imports()
        test2_label.setText(f"Test 2: {test2_result}")
        layout.addWidget(test2_label)
        
        # Test 3: Create visualization
        test3_btn = QPushButton("Test 3: Create VisualizationWindow")
        test3_btn.clicked.connect(self.test_visualization_creation)
        layout.addWidget(test3_btn)
        
    def test_file_existence(self):
        excel_file = "封装连线示意.xlsx"
        exists = os.path.exists(excel_file)
        return f"File exists: {exists}" if exists else f"File NOT found: {excel_file}"
    
    def test_module_imports(self):
        try:
            from data_handlers import ExcelHandler
            from ui import VisualizationWindow
            return "All modules imported successfully"
        except Exception as e:
            return f"Import error: {e}"
    
    def test_visualization_creation(self):
        try:
            from data_handlers import ExcelHandler
            from ui import VisualizationWindow
            
            handler = ExcelHandler()
            excel_file = "封装连线示意.xlsx"
            
            if handler.read_excel(excel_file):
                pads = handler.get_pads()
                print(f"Loaded {len(pads)} pads")
                
                viz_window = VisualizationWindow(pads)
                print("VisualizationWindow created")
                viz_window.show()
                print("VisualizationWindow.show() called")
            else:
                print("Failed to read Excel file")
                
        except Exception as e:
            print(f"Error in test_visualization_creation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    debug_window = DebugWindow()
    debug_window.show()
    
    sys.exit(app.exec_())
