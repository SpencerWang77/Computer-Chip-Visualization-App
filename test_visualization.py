import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from data_handlers import ExcelHandler
from ui import VisualizationWindow


def test_visualization():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(245, 246, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)
    
    handler = ExcelHandler()
    excel_file = "封装连线示意.xlsx"
    
    if handler.read_excel(excel_file):
        pads = handler.get_pads()
        print(f"Loaded {len(pads)} pads for visualization")
        
        viz_window = VisualizationWindow(pads)
        viz_window.show()
        
        sys.exit(app.exec_())
    else:
        print("Failed to load Excel file")


if __name__ == "__main__":
    test_visualization()
