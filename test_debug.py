from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from data_handlers import ExcelHandler
from ui import VisualizationWindow

def test_debug_output():
    app = QApplication([])
    app.setStyle('Fusion')
    
    handler = ExcelHandler()
    excel_file = "封装连线示意.xlsx"
    
    if handler.read_excel(excel_file):
        pads = handler.get_pads()
        print(f"Loading {len(pads)} pads into visualization...")
        
        viz_window = VisualizationWindow(pads[:5])  # 只测试前5个
        viz_window.show()
        
        print("Visualization window created with debug output")
        app.exec_()
    else:
        print("Failed to load Excel file")

if __name__ == "__main__":
    test_debug_output()
