from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PyQt5.QtCore import Qt
from data_handlers import ExcelHandler

def test_simple_creation():
    app = QApplication([])
    app.setStyle('Fusion')
    
    # 创建简单场景
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 300, 200)
    
    # 添加背景
    from PyQt5.QtWidgets import QGraphicsRectItem
    from PyQt5.QtGui import QPen, QBrush, QColor
    
    bg = QGraphicsRectItem(0, 0, 300, 200)
    bg.setBrush(QBrush(QColor(236, 240, 241)))
    bg.setPen(QPen(QColor(189, 195, 199), 2))
    scene.addItem(bg)
    
    # 创建一个简单的测试pad
    from ui.chip_visualization import PadGraphicsItem
    from models import Pad
    
    test_pad = Pad("SOC.1", "TEST", 50, 50, 45.9, 79.2, "VCC", "LF.119")
    pad_item = PadGraphicsItem(test_pad, 10, 10, 45.9, 79.2)
    scene.addItem(pad_item)
    
    print(f"Test pad created: {test_pad.pad_id}")
    print(f"Scene has {len(scene.items())} items")
    
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.setGeometry(100, 100, 400, 300)
    view.show()
    
    print("View shown - you should see a blue rectangle with number 1")
    
    app.exec_()

if __name__ == "__main__":
    from PyQt5.QtGui import QPainter
    test_simple_creation()
