from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                              QGraphicsView, QWidget, QVBoxLayout, QLabel, QLineEdit,
                              QPushButton, QHBoxLayout, QGraphicsLineItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter
from models import Pad, ChipLayout


class PadGraphicsItem(QGraphicsRectItem):
    def __init__(self, pad: Pad, x: float, y: float, width: float, height: float, fill_color=None):
        super().__init__(x, y, width, height)
        self.pad = pad
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        
        # 禁用悬停效果
        self.setAcceptHoverEvents(False)
        
        # 使用指定的填充颜色，如果没有提供则使用默认
        if fill_color is None:
            fill_color = QColor(52, 152, 219, 200)
        
        # 设置边框和填充颜色
        pen = QPen(QColor(41, 128, 185), 3)
        self.setPen(pen)
        self.setBrush(QBrush(fill_color))
        self._original_brush = QBrush(fill_color)  # 保存原始颜色
        
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
                # 被选中时只改变边框颜色，不改填充颜色
                self.setPen(QPen(QColor(241, 196, 15), 5))  # 橙色加粗边框
            else:
                # 取消选中时恢复原始边框
                self.setPen(QPen(QColor(41, 128, 185), 3))  # 恢复深蓝色边框
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
    



class ChipScene(QGraphicsScene):
    pad_clicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pad_items = {}
        self.chip_layout = ChipLayout()
        self._lf_color_map = {}  # 存储LF到颜色的映射
    
    def _get_pad_fill_color(self, pad: Pad) -> QColor:
        """根据bonding关系获取pad的填充颜色"""
        bonding = pad.bonding if hasattr(pad, 'bonding') else ""
        bonding_upper = bonding.upper()
        
        # 规则1: Not Bond -> 黑色
        if bonding_upper == "NOT_BOND" or bonding_upper == "NOT BOND" or bonding_upper == "":
            return QColor(33, 33, 33, 200)  # 黑色
        
        # 规则2: E-pad或VSS_ring -> 深蓝色
        if "E_PAD" in bonding_upper or "E-PAD" in bonding_upper or "E PAD" in bonding_upper:
            return QColor(41, 128, 185, 200)  # 深蓝色
        if "VSS_RING" in bonding_upper or "VSS_RING" in bonding_upper or "VSS RING" in bonding_upper:
            return QColor(41, 128, 185, 200)  # 深蓝色
        
        # 规则3: LF -> 浅色，相同LF使用相同颜色
        if "LF" in bonding_upper:
            # 提取LF的唯一标识符
            lf_key = self._extract_lf_key(bonding_upper)
            if lf_key not in self._lf_color_map:
                # 分配一个新的浅色
                self._lf_color_map[lf_key] = self._get_next_lf_color()
            return self._lf_color_map[lf_key]
        
        # 规则4: SOC, PSRAM, DDRA, DDRB, ROM -> 深灰色
        if bonding_upper in ["SOC", "PSRAM", "DDRA", "DDRB", "ROM"] or "ROM" in bonding_upper or "DDRA" in bonding_upper or "DDRB" in bonding_upper:
            return QColor(80, 80, 80, 200)  # 深灰色
        
        # 规则5: 未定义或无法分类 -> 深红色
        return QColor(192, 57, 43, 200)  # 深红色
    
    def _extract_lf_key(self, bonding_upper: str) -> str:
        """从bonding字符串中提取LF的唯一标识符"""
        # 查找LF及其相关标识
        import re
        # 匹配LF后面跟着数字或字母的模式（包括LF.10格式）
        match = re.search(r'LF[._\s]*([A-Z0-9]+)', bonding_upper)
        if match:
            lf_num = match.group(1)
            return f"LF_{lf_num}"
        return "LF_DEFAULT"
    
    def _get_next_lf_color(self) -> QColor:
        """获取下一个LF用的浅色（只用2-3种，确保不接近白色）"""
        lf_colors = [
            (150, 205, 150, 200),  # 中等绿色 - 避免太亮
            (135, 206, 250, 200),  # 中等蓝色 - 避免太亮
            (250, 160, 122, 200),  # 珊瑚色 - 适当的对比度
        ]
        used_colors = list(self._lf_color_map.values())
        
        # 循环使用3种颜色
        used_count = len(self._lf_color_map)
        color_index = used_count % len(lf_colors)
        return QColor(*lf_colors[color_index])
    
    def set_pads(self, pads, frame_params=None):
        self.clear()
        self.chip_layout.set_pads(pads)
        self._lf_color_map = {}  # 清空LF颜色映射
        
        coords_info = self.chip_layout.get_expanded_coordinates()
        
        # 先绘制框架（如果有参数的话）
        if frame_params and frame_params.get('die_width') and frame_params.get('die_height') and frame_params.get('lf_count'):
            frame_coords = self._draw_frame_board(frame_params)
            # 使用框架的坐标范围来设置场景矩形
            self.setSceneRect(frame_coords['min_x'] - 100, frame_coords['min_y'] - 100, 
                             frame_coords['width'] + 200, frame_coords['height'] + 200)
        else:
            # 如果没有框架，使用原来的die坐标
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
    
    def _draw_frame_board(self, frame_params):
        """绘制框架板（Leadframe）"""
        die_width = frame_params['die_width']
        die_height = frame_params['die_height']
        lf_count = frame_params['lf_count']
        
        # 计算框架尺寸（框架比die大一圈，留出引脚空间）
        frame_margin = 180  # 引言和框架边距，单位μm（更接近die）
        boarder_thickness = 100  # 框架厚度
        pin_length = 60  # 引脚长度（用于计算外边界）
        
        # 计算框架板的总尺寸
        frame_width = die_width + 2 * frame_margin + 2 * boarder_thickness
        frame_height = die_height + 2 * frame_margin + 2 * boarder_thickness
        
        # 获取当前的中心位置
        coords_info = self.chip_layout.get_expanded_coordinates()
        center_x = coords_info['min_x'] + coords_info['width'] / 2
        center_y = coords_info['min_y'] + coords_info['height'] / 2
        
        # 计算框架板的左上角位置
        frame_min_x = center_x - frame_width / 2
        frame_min_y = center_y - frame_height / 2
        
        # 绘制外框架（矩形边框）
        frame_rect = QGraphicsRectItem(
            frame_min_x, frame_min_y, frame_width, frame_height
        )
        frame_rect.setPen(QPen(QColor(52, 73, 94, 255), boarder_thickness))  # 深灰色边框
        frame_rect.setBrush(QBrush(Qt.NoBrush))  # 不填充，只显示边框
        self.addItem(frame_rect)
        
        # 计算引脚位置
        if lf_count >= 4:
            # 计算每边的LF数量（4边平分）
            lf_per_side = lf_count // 4
            
            # 绘制引脚标记
            self._draw_leadframe_pins(
                frame_min_x, frame_min_y, frame_width, frame_height, 
                frame_margin, boarder_thickness, lf_per_side
            )
        
        # 返回框架的完整坐标范围（包括引脚）
        return {
            'min_x': frame_min_x - pin_length,
            'min_y': frame_min_y - pin_length,
            'width': frame_width + 2 * pin_length,
            'height': frame_height + 2 * pin_length
        }
    
    def _draw_leadframe_pins(self, frame_min_x, frame_min_y, frame_width, frame_height, 
                            frame_margin, boarder_thickness, lf_per_side):
        """绘制Leadframe引脚标记"""
        from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem
        
        # 引脚绘制参数
        pin_length = 60  # 引脚长度
        pin_width = 30   # 引脚厚度
        pin_edge_offset = frame_margin + boarder_thickness / 2  # 引脚边缘偏移
        
        # 引脚编号计数器
        pin_counter = 1
        
        # 绘制四边的引脚（按照要求的顺序：左、下、右、上）
        # 左边：从上往下
        if lf_per_side > 0:
            effective_height = frame_height - 2 * pin_edge_offset
            spacing = effective_height / (lf_per_side + 1)
            
            for i in range(1, lf_per_side + 1):
                pin_y = frame_min_y + pin_edge_offset + i * spacing
                
                pin = QGraphicsLineItem(frame_min_x - pin_length, pin_y, frame_min_x, pin_y)
                pen = QPen(QColor(70, 80, 90, 200), pin_width)
                pen.setCapStyle(Qt.RoundCap)
                pin.setPen(pen)
                self.addItem(pin)
                
                self._draw_lf_label(frame_min_x - pin_length - 50, pin_y - 10, pin_counter)
                pin_counter += 1
        
        # 下边：从左往右
        if lf_per_side > 0:
            effective_width = frame_width - 2 * pin_edge_offset
            spacing = effective_width / (lf_per_side + 1)
            
            for i in range(1, lf_per_side + 1):
                pin_x = frame_min_x + pin_edge_offset + i * spacing
                
                pin = QGraphicsLineItem(pin_x, frame_min_y + frame_height, pin_x, frame_min_y + frame_height + pin_length)
                pen = QPen(QColor(70, 80, 90, 200), pin_width)
                pen.setCapStyle(Qt.RoundCap)
                pin.setPen(pen)
                self.addItem(pin)
                
                self._draw_lf_label(pin_x - 15, frame_min_y + frame_height + pin_length + 5, pin_counter)
                pin_counter += 1
        
        # 右边：从下往上
        if lf_per_side > 0:
            effective_height = frame_height - 2 * pin_edge_offset
            spacing = effective_height / (lf_per_side + 1)
            
            for i in range(lf_per_side, 0, -1):
                pin_y = frame_min_y + pin_edge_offset + i * spacing
                
                pin = QGraphicsLineItem(frame_min_x + frame_width, pin_y, frame_min_x + frame_width + pin_length, pin_y)
                pen = QPen(QColor(70, 80, 90, 200), pin_width)
                pen.setCapStyle(Qt.RoundCap)
                pin.setPen(pen)
                self.addItem(pin)
                
                self._draw_lf_label(frame_min_x + frame_width + pin_length + 10, pin_y - 10, pin_counter)
                pin_counter += 1
        
        # 上边：从右往左
        if lf_per_side > 0:
            effective_width = frame_width - 2 * pin_edge_offset
            spacing = effective_width / (lf_per_side + 1)
            
            for i in range(lf_per_side, 0, -1):
                pin_x = frame_min_x + pin_edge_offset + i * spacing
                
                pin = QGraphicsLineItem(pin_x, frame_min_y - pin_length, pin_x, frame_min_y)
                pen = QPen(QColor(70, 80, 90, 200), pin_width)
                pen.setCapStyle(Qt.RoundCap)
                pin.setPen(pen)
                self.addItem(pin)
                
                self._draw_lf_label(pin_x - 15, frame_min_y - pin_length - 25, pin_counter)
                pin_counter += 1
    
    def _draw_lf_label(self, x: float, y: float, number: int):
        """绘制LF标签（LF.1, LF.2等格式）"""
        text = QGraphicsTextItem(f"LF.{number}")
        font = QFont("Arial", 14, QFont.Bold)  # 从8放大到14
        text.setFont(font)
        text.setDefaultTextColor(QColor(70, 80, 90, 200))
        text.setPos(x, y)
        self.addItem(text)
    
    def _draw_pads(self):
        coords_info = self.chip_layout.get_expanded_coordinates()
        pads = self.chip_layout.pads
        
        for pad in pads:
            rect_info = self.chip_layout.get_pad_rectangle(pad.pad_id)
            if rect_info:
                x1, y1, x2, y2 = rect_info
                
                width = x2 - x1
                height = y2 - y1
                
                # 根据bonding关系获取填充颜色
                fill_color = self._get_pad_fill_color(pad)
                
                pad_item = PadGraphicsItem(pad, x1, y1, width, height, fill_color)
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
    
    def fit_in_view(self):
        """自动缩放到整个场景范围"""
        if self.scene():
            # 获取场景矩形
            scene_rect = self.scene().sceneRect()
            if not scene_rect.isNull():
                # 添加一些边距
                margin = 20
                fitted_rect = scene_rect.adjusted(-margin, -margin, margin, margin)
                # 适应视图
                self.fitInView(fitted_rect, Qt.KeepAspectRatio)
