import sys

# 直接运行PyQt应用，使用交互式方式输入命令查看输出
print("Testing PyQt5 text display...")

from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter

app = QApplication([])
scene = QGraphicsScene()
scene.setSceneRect(0, 0, 300, 200)

# 添加矩形
rect = QGraphicsRectItem(50, 50, 100, 80)
rect.setBrush(QBrush(QColor(52, 152, 219)))
rect.setPen(QPen(QColor(41, 128, 185), 3))
scene.addItem(rect)

# 添加文本
text = QGraphicsTextItem("1", rect)
text.setFont(QFont("Arial", 20, QFont.Bold))
text.setDefaultTextColor(QColor(255, 255, 255))
text.setZValue(10)
text.setVisible(True)

print(f"Text created: {text.toPlainText()}")
print(f"Text position: ({text.x()}, {text.y()})")
print(f"Rect position: ({rect.x()}, {rect.y()})")

view = QGraphicsView(scene)
view.setRenderHint(QPainter.Antialiasing)
view.setRenderHint(QPainter.TextAntialiasing)
view.show()

print("Application started - you should see a blue rectangle with '1' inside")
sys.exit(app.exec_())
