import sys
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter
from data_handlers import ExcelHandler

def test_text_rendering():
    print("Starting text rendering test...")
    
    app = QApplication([])
    app.setStyle('Fusion')
    
    # 加载数据
    handler = ExcelHandler()
    handler.read_excel("封装连线示意.xlsx")
    pads = handler.get_pads()
    
    print(f"Loaded {len(pads)} pads")
    
    # 创建场景
    scene = QGraphicsScene()
    scene.setSceneRect(-100, -100, 600, 500)
    
    # 添加背景
    bg = QGraphicsRectItem(-100, -100, 600, 500)
    bg.setBrush(QBrush(QColor(236, 240, 241)))
    bg.setPen(QPen(QColor(189, 195, 199), 2))
    scene.addItem(bg)
    
    # 绘制前5个pads
    from models import ChipLayout
    chip_layout = ChipLayout()
    chip_layout.set_pads(pads)
    
    for i, pad in enumerate(pads[:5]):
        rect_info = chip_layout.get_pad_rectangle(pad.pad_id)
        if rect_info:
            x1, y1, x2, y2 = rect_info
            width = x2 - x1
            height = y2 - y1
            
            print(f"\n{i+1}. Creating pad for {pad.pad_id}:")
            print(f"   Rectangle: ({x1:.2f}, {y1:.2f}) to ({x2:.2f}, {y2:.2f})")
            print(f"   Size: {width:.2f} x {height:.2f}")
            
            # 提取数字
            parts = pad.pad_id.split('.')
            pad_number = parts[-1] if len(parts) > 1 else str(pad.pad_id)
            
            print(f"   SOC number: {pad_number}")
            
            # 创建矩形
            rect_item = QGraphicsRectItem(x1, y1, width, height)
            rect_item.setBrush(QBrush(QColor(52, 152, 219)))
            rect_item.setPen(QPen(QColor(41, 128, 185), 3))
            scene.addItem(rect_item)
            
            # 计算字体大小
            font_size = max(25, int(min(width, height) / 2))
            print(f"   Font size: {font_size}")
            
            # 创建文本
            text = QGraphicsTextItem(pad_number)
            font = QFont("Arial", font_size, QFont.Bold)
            text.setFont(font)
            text.setDefaultTextColor(QColor(255, 255, 255))
            text.setZValue(100)
            text.setVisible(True)
            text.setOpacity(1.0)
            
            # 计算文本位置
            text_rect = text.boundingRect()
            text_x = x1 + (width - text_rect.width()) / 2
            text_y = y1 + (height - text_rect.height()) / 2
            
            print(f"   Text rectangle: {text_rect.width():.2f} x {text_rect.height():.2f}")
            print(f"   Text position: ({text_x:.2f}, {text_y:.2f})")
            print(f"   Text content: '{text.toPlainText()}'")
            print(f"   Text visible: {text.isVisible()}")
            
            text.setPos(text_x, text_y)
            scene.addItem(text)
            
            print(f"   OK Text added to scene")
    
    # 创建视图
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    view.scale(2.0, 2.0)  # 放大2倍确保文字可见
    view.setGeometry(100, 100, 800, 600)
    view.show()
    
    print(f"\nScene now has {len(scene.items())} items")
    print(f"You should see {min(5, len(pads))} blue rectangles with white numbers inside")
    print("Check each rectangle from SOC.1 to SOC.5")
    
    app.exec_()

if __name__ == "__main__":
    test_text_rendering()
