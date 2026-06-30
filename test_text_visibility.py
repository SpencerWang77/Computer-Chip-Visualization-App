from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter

def test_text_visibility():
    print("Starting text visibility test...")
    
    app = QApplication([])
    app.setStyle('Fusion')
    
    # 创建场景
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 400, 300)
    
    # 添加背景
    bg = QGraphicsRectItem(0, 0, 400, 300)
    bg.setBrush(QBrush(QColor(236, 240, 241)))
    bg.setPen(QPen(QColor(189, 195, 199), 2))
    scene.addItem(bg)
    
    # 添加一个测试pad矩形
    test_rect = QGraphicsRectItem(50, 50, 100, 80)
    test_rect.setBrush(QBrush(QColor(52, 152, 219, 200)))
    test_rect.setPen(QPen(QColor(41, 128, 185), 3))
    scene.addItem(test_rect)
    
    # 添加文本
    print("Creating text item...")
    text = QGraphicsTextItem("123", test_rect)
    font = QFont("Arial", 20, QFont.Bold)
    text.setFont(font)
    text.setDefaultTextColor(QColor(255, 255, 255))
    text.setZValue(10)
    text.setVisible(True)
    
    # 居中文本
    text_rect = text.boundingRect()
    text_x = (100 - text_rect.width()) / 2
    text_y = (80 - text_rect.height()) / 2
    text.setPos(text_x, text_y)
    
    print(f"Text: {text.toPlainText()}")
    print(f"Font: {text.font().pointSize()}")
    print(f"Position: ({text.x()}, {text.y()})")
    print(f"Visible: {text.isVisible()}")
    print(f"Opacity: {text.opacity()}")
    
    # 创建视图
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    view.setGeometry(100, 100, 600, 500)
    view.show()
    
    print("View created and shown")
    print("You should see a blue rectangle with '123' in white bold text")
    
    app.exec_()

if __name__ == "__main__":
    test_text_visibility()
