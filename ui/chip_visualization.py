from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                             QGraphicsView, QWidget, QVBoxLayout, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter
from models import Pad, ChipLayout


class PadGraphicsItem(QGraphicsRectItem):
    def __init__(self, pad: Pad, x: float, y: float, width: float, height: float):
        super().__init__(x, y, width, height)
        self.pad = pad
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        
        # 禁用悬停效果
        self.setAcceptHoverEvents(False)
        
        # 深蓝色背景，加粗边框
        pen = QPen(QColor(41, 128, 185), 3)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(52, 152, 219, 200)))
        
        # 获取pad编号
        self._pad_number = self._get_pad_id_text()
        
        # 根据数字位数和pad尺寸动态计算字体大小
        num_digits = len(self._pad_number)
        
        # 基础字体大小计算
        min_dim = min(width, height)
        
        # 根据位数调整字体大小 - 更精确的控制
        if num_digits == 1:
            font_size = min_dim / 1.8  # 单位数：最大字体，留适当余量
        elif num_digits == 2:
            font_size = min_dim / 2.5  # 两位数：适当缩小
        else:  # 3位及以上
            font_size = min_dim / 3.5  # 多位数：大幅缩小，确保能完全放下
        
        font_size = max(12, int(font_size))  # 最小12像素字体
        
        # 创建文本项 - 不作为子项，直接添加到场景
        self.text_item = QGraphicsTextItem(str(self._pad_number))
        font = QFont("Arial", font_size, QFont.Bold)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setZValue(100)  # 确保文本在最上层
        self.text_item.setVisible(True)
        self.text_item.setOpacity(1.0)
        
        # 获取文本尺寸
        text_rect = self.text_item.boundingRect()
        
        # 自适应调整：如果文本超出边界，进一步缩小字体
        max_attempts = 3
        for attempt in range(max_attempts):
            text_rect = self.text_item.boundingRect()
            
            # 检查文本是否超出矩形边界
            if (text_rect.width() > width * 0.9 or 
                text_rect.height() > height * 0.9):
                # 减小字体尺寸
                current_font = self.text_item.font()
                new_size = max(8, int(current_font.pointSize() * 0.8))
                current_font.setPointSize(new_size)
                self.text_item.setFont(current_font)
            else:
                break
        
        # 重新获取最终的文本尺寸
        final_text_rect = self.text_item.boundingRect()
        
        # 计算文本居中位置 - 相对于矩形的绝对坐标
        text_x = x + (width - final_text_rect.width()) / 2
        text_y = y + (height - final_text_rect.height()) / 2
        
        # 确保文本不会越界
        text_x = max(x, min(text_x, x + width - final_text_rect.width()))
        text_y = max(y, min(text_y, y + height - final_text_rect.height()))
        
        self.text_item.setPos(text_x, text_y)
        
        # 调试信息保存
        self._debug_info = {
            'pad_id': pad.pad_id,
            'pad_number': self._pad_number,
            'rect_pos': (x, y),
            'rect_size': (width, height),
            'text_pos': (text_x, text_y),
            'font_size': font_size,
            'text_rect': (text_rect.width(), text_rect.height())
        }
    
    def _get_pad_id_text(self):
        parts = self.pad.pad_id.split('.')
        return parts[-1] if len(parts) > 1 else self.pad.pad_id
    
    def get_debug_info(self):
        return hasattr(self, '_debug_info') and self._debug_info or {}
    
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            if value:
                # 被选中时改变颜色
                self.setBrush(QBrush(QColor(241, 196, 15, 200)))
            else:
                # 取消选中时恢复原色
                self.setBrush(QBrush(QColor(52, 152, 219, 200)))
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        # 选中时清除场景中其他项目的选中状态
        if self.scene():
            for item in self.scene().selectedItems():
                if item != self:
                    item.setSelected(False)
        
        # 设置当前项目为选中状态
        self.setSelected(True)
        
        # 触发点击信号
        if self.scene() and hasattr(self.scene(), 'pad_clicked'):
            self.scene().pad_clicked.emit(self.pad)
        
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(39, 174, 96, 120)))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(52, 152, 219, 80)))
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        self.setSelected(True)
        super().mousePressEvent(event)


class ChipScene(QGraphicsScene):
    pad_clicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pad_items = {}
        self.chip_layout = ChipLayout()
    
    def set_pads(self, pads):
        self.clear()
        self.chip_layout.set_pads(pads)
        
        coords_info = self.chip_layout.get_expanded_coordinates()
        self.setSceneRect(coords_info['min_x'], coords_info['min_y'], 
                         coords_info['width'], coords_info['height'])
        
        self._draw_chip_board()
        self._draw_pads()
    
    def _draw_chip_board(self):
        coords_info = self.chip_layout.get_expanded_coordinates()
        chip_rect = QGraphicsRectItem(
            coords_info['min_x'], coords_info['min_y'], 
            coords_info['width'], coords_info['height']
        )
        
        # 更美观的浅色芯片板背景
        chip_rect.setPen(QPen(QColor(189, 195, 199), 2))
        chip_rect.setBrush(QBrush(QColor(236, 240, 241, 255)))
        self.addItem(chip_rect)
    
    def _draw_pads(self):
        coords_info = self.chip_layout.get_expanded_coordinates()
        pads = self.chip_layout.pads
        
        for pad in pads:
            rect_info = self.chip_layout.get_pad_rectangle(pad.pad_id)
            if rect_info:
                x1, y1, x2, y2 = rect_info
                
                width = x2 - x1
                height = y2 - y1
                
                pad_item = PadGraphicsItem(pad, x1, y1, width, height)
                self.addItem(pad_item)
                
                # 单独添加文本项到场景
                if hasattr(pad_item, 'text_item'):
                    self.addItem(pad_item.text_item)
                    # 将文本项与pad关联
                    pad_item.text_item.setData(0, pad.pad_id)
                
                self.pad_items[pad.pad_id] = pad_item
    
    def mousePressEvent(self, event):
        pos = event.scenePos()
        items = self.items(pos)
        
        for item in items:
            if isinstance(item, PadGraphicsItem):
                self.pad_clicked.emit(item.pad)
                return
        
        super().mousePressEvent(event)


class PadInfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pad = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.info_label = QLabel("点击pad查看详细信息")
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                color: #2c3e50;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(self.info_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: none;
            }
        """)
    
    def show_pad_info(self, pad: Pad):
        self.current_pad = pad
        
        info_text = f"""
        <b>Pad详细信息</b>
        <hr style='color: #3498db;'>
        <b>Pad ID:</b> {pad.pad_id}<br>
        <b>Pad名称:</b> {pad.pad_name}<br>
        <b>坐标位置:</b> ({pad.x_coord:.4f}, {pad.y_coord:.4f})<br>
        <b>尺寸 (X×Y):</b> {pad.x_open:.2f} × {pad.y_open:.2f}<br>
        <b>网络名称:</b> {pad.net_name}<br>
        <b>焊接关系:</b> {pad.bonding}
        """
        
        self.info_label.setText(info_text)
    
    def clear_info(self):
        self.current_pad = None
        self.info_label.setText("点击pad查看详细信息")


class ChipVisualizationView(QGraphicsView):
    def __init__(self, scene: ChipScene, parent=None):
        super().__init__(scene, parent)
        
        # 启用多种渲染优化
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # 优化视图更新
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # 禁用滚动条的双缓冲
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
    
    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        self.scale(zoom_factor, zoom_factor)
