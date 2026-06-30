import sys

# 重定向输出到文件
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter

# 创建文件用于输出日志
log_file = open("visualization_log.txt", "w", encoding='utf-8')
sys.stdout = log_file

try:
    print("Starting PyQt5 application...")
    
    app = QApplication([])
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 300, 200)
    
    # 添加矩形
    rect = QGraphicsRectItem(50, 50, 100, 80)
    rect.setBrush(QBrush(QColor(52, 152, 219)))
    rect.setPen(QPen(QColor(41, 128, 185), 3))
    scene.addItem(rect)
    print(f"Rectangle added at ({rect.x()}, {rect.y()}) with size {rect.rect().width()}x{rect.rect().height()}")
    
    # 添加文本
    text = QGraphicsTextItem("1", rect)
    text.setFont(QFont("Arial", 24, QFont.Bold))
    text.setDefaultTextColor(QColor(255, 255, 255))
    text.setZValue(10)
    text.setVisible(True)
    print(f"Text item created with content: '{text.toPlainText()}'")
    print(f"Text font size: {text.font().pointSize()}")
    print(f"Text position: ({text.x()}, {text.y()})")
    print(f"Text visible: {text.isVisible()}")
    
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.show()
    
    print("View shown - application should display a blue rectangle with number 1")
    print(f"Scene has {len(scene.items())} items")
    
    # 刷新日志文件
    log_file.flush()
    
    app.exec_()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    log_file.close()
