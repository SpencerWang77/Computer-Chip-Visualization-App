import sys
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter

def test_three_digit_display():
    print("Testing three-digit number display...")
    
    app = QApplication([])
    app.setStyle('Fusion')
    
    # 创建场景
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 500, 400)
    
    # 添加深蓝色背景便于观察
    bg = QGraphicsRectItem(0, 0, 500, 400)
    bg.setBrush(QBrush(QColor(30, 30, 30)))
    scene.addItem(bg)
    
    # 测试不同位数的数字在最小pad尺寸下的显示
    test_cases = [
        ("1", "SOC.1 (1-digit)"),
        ("12", "SOC.12 (2-digit)"),
        ("123", "SOC.123 (3-digit)"),
        ("99", "SOC.99 (2-digit max)"),
        ("100", "SOC.100 (3-digit min)")
    ]
    
    pad_size = 45.9  # 最小pad尺寸
    start_y = 50
    start_x = 50
    spacing_y = 70
    
    for i, (number, description) in enumerate(test_cases):
        y_pos = start_y + i * spacing_y
        
        # 创建pad矩形
        rect_item = QGraphicsRectItem(start_x, y_pos, pad_size, pad_size)
        rect_item.setBrush(QBrush(QColor(52, 152, 219)))
        rect_item.setPen(QPen(QColor(41, 128, 185), 2))
        scene.addItem(rect_item)
        
        # 计算字体大小
        num_digits = len(number)
        if num_digits == 1:
            font_size = pad_size / 2.0
        elif num_digits == 2:
            font_size = pad_size / 2.8
        else:
            font_size = pad_size / 4.0
        
        font_size = max(10, int(font_size))
        
        # 创建文本
        text = QGraphicsTextItem(number)
        font = QFont("Arial", font_size, QFont.Bold)
        text.setFont(font)
        text.setDefaultTextColor(QColor(255, 255, 255))
        text.setZValue(100)
        
        # 居中放置
        text_rect = text.boundingRect()
        text_x = start_x + (pad_size - text_rect.width()) / 2
        text_y = y_pos + (pad_size - text_rect.height()) / 2
        text.setPos(text_x, text_y)
        scene.addItem(text)
        
        # 添加说明文字
        label = QGraphicsTextItem(description)
        label.setFont(QFont("Arial", 10))
        label.setDefaultTextColor(QColor(200, 200, 200))
        label.setPos(start_x + pad_size + 20, y_pos + 15)
        scene.addItem(label)
        
        print(f"{description}: Font size = {font_size:.1f}, Text size = {text_rect.width():.1f}x{text_rect.height():.1f}")
    
    # 创建视图
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    view.setGeometry(100, 100, 800, 600)
    view.show()
    
    print("\nDisplay test started - check if numbers fit properly in the blue rectangles")
    print("From top to bottom: 1-digit, 2-digit, 3-digit, max 2-digit, min 3-digit")
    
    app.exec_()

if __name__ == "__main__":
    test_three_digit_display()
