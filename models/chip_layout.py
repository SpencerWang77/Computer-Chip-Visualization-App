from typing import List, Tuple, Optional
from models import Pad


class ChipLayout:
    def __init__(self):
        self.chip_size = (800, 500)  # 芯片板尺寸 (宽, 高)
        self.pads: List[Pad] = []
        self.pad_rectangles = {}  # 存储pad对应的矩形信息
        
    def set_pads(self, pads: List[Pad]):
        self.pads = pads
        self._calculate_layout()
        
        # 移除已删除的pad
        self._remove_deleted_pads()
    
    def _calculate_layout(self):
        self.pad_rectangles = {}
        
        if not self.pads:
            return
        
        for pad in self.pads:
            if not pad.is_marked_for_deletion:
                center_x = pad.x_coord
                center_y = pad.y_coord
                width = pad.x_open
                height = pad.y_open
                
                x1 = center_x - width / 2
                y1 = center_y - height / 2
                x2 = center_x + width / 2
                y2 = center_y + height / 2
                
                self.pad_rectangles[pad.pad_id] = (x1, y1, x2, y2)
    
    def _remove_deleted_pads(self):
        """移除标记为删除的pad"""
        self.pads = [pad for pad in self.pads if not pad.is_marked_for_deletion()]
        # 重新计算布局
        self._calculate_layout()
    
    # CRUD 操作方法
    def add_pad(self, pad: Pad) -> bool:
        """添加一个新的pad"""
        # 检查pad_id是否已存在
        if any(p.pad_id == pad.pad_id for p in self.pads):
            return False  # pad_id已存在
        
        self.pads.append(pad)
        self._calculate_layout()
        return True
    
    def remove_pad(self, pad_id: str) -> bool:
        """移除指定ID的pad"""
        for i, pad in enumerate(self.pads):
            if pad.pad_id == pad_id:
                self.pads.pop(i)
                self._calculate_layout()
                return True
        return False  # pad不存在
    
    def update_pad(self, pad_id: str, **kwargs) -> bool:
        """更新指定ID的pad属性"""
        for pad in self.pads:
            if pad.pad_id == pad_id:
                # 更新属性
                if 'pad_name' in kwargs:
                    pad.pad_name = kwargs['pad_name']
                if 'x_coord' in kwargs:
                    pad.x_coord = float(kwargs['x_coord'])
                if 'y_coord' in kwargs:
                    pad.y_coord = float(kwargs['y_coord'])
                if 'x_open' in kwargs:
                    pad.x_open = float(kwargs['x_open'])
                if 'y_open' in kwargs:
                    pad.y_open = float(kwargs['y_open'])
                if 'net_name' in kwargs:
                    pad.net_name = kwargs['net_name']
                if 'bonding' in kwargs:
                    pad.bonding = kwargs['bonding']
                
                pad.mark_as_modified()
                self._calculate_layout()
                return True
        return False  # pad不存在
    
    def replace_pad(self, old_pad_id: str, new_pad: Pad) -> bool:
        """替换指定ID的pad"""
        for i, pad in enumerate(self.pads):
            if pad.pad_id == old_pad_id:
                self.pads[i] = new_pad
                self._calculate_layout()
                return True
        return False  # 旧pad不存在
    
    def get_pad_by_id(self, pad_id: str) -> Optional[Pad]:
        """根据ID获取pad对象"""
        for pad in self.pads:
            if pad.pad_id == pad_id:
                return pad
        return None
    
    def get_all_pads(self) -> List[Pad]:
        """获取所有pad"""
        return self.pads.copy()
    
    def get_modified_pads(self) -> List[Pad]:
        """获取所有被修改过的pad"""
        return [pad for pad in self.pads if pad.is_modified]
    
    def get_pads_to_delete(self) -> List[Pad]:
        """获取所有标记为删除的pad"""
        return [pad for pad in self.pads if pad.is_marked_for_deletion]
    
    # 原有方法
    def get_chip_size(self) -> Tuple[float, float]:
        return self.chip_size
    
    def get_pad_rectangle(self, pad_id: str) -> Tuple[float, float, float, float]:
        return self.pad_rectangles.get(pad_id, (0, 0, 0, 0))
    
    def get_pad_at_position(self, x: float, y: float) -> Optional[Pad]:
        for pad in self.pads:
            rect_info = self.pad_rectangles.get(pad.pad_id)
            if rect_info:
                x1, y1, x2, y2 = rect_info
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return pad
        return None
    
    def get_expanded_coordinates(self):
        if not self.pads:
            return {'min_x': 0, 'max_x': 800, 'min_y': 0, 'max_y': 500, 'width': 800, 'height': 500}
        
        coords = [(pad.x_coord, pad.y_coord) for pad in self.pads]
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]
        
        min_x = min(x_coords) - 50
        max_x = max(x_coords) + 50
        min_y = min(y_coords) - 50
        max_y = max(y_coords) + 50
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
