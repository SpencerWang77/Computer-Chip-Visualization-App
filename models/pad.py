class Pad:
    def __init__(self, pad_id, pad_name, x_coord, y_coord, x_open, y_open, net_name, bonding):
        self.pad_id = pad_id
        self.pad_name = pad_name
        self.x_coord = float(x_coord) if x_coord else 0.0
        self.y_coord = float(y_coord) if y_coord else 0.0
        self.x_open = float(x_open) if x_open else 0.0
        self.y_open = float(y_open) if y_open else 0.0
        self.net_name = net_name if net_name else ""
        self.bonding = bonding if bonding else ""
        
        # 模块化状态标记
        self._modified = False
        self._marked_for_deletion = False
    
    @property
    def is_modified(self):
        """检查pad是否被修改过"""
        return self._modified
    
    def is_marked_for_deletion(self):
        """检查pad是否被标记为删除"""
        return self._marked_for_deletion
    
    def mark_as_modified(self):
        """标记pad为已修改"""
        self._modified = True
    
    def reset_modified_status(self):
        """重置修改状态"""
        self._modified = False
    
    def mark_for_deletion(self):
        """标记pad为待删除"""
        self._marked_for_deletion = True
    
    def unmark_for_deletion(self):
        """取消删除标记"""
        self._marked_for_deletion = False
    
    def update_position(self, x_coord=None, y_coord=None):
        """更新坐标位置"""
        if x_coord is not None:
            self.x_coord = float(x_coord)
        if y_coord is not None:
            self.y_coord = float(y_coord)
        self.mark_as_modified()
    
    def update_size(self, x_open=None, y_open=None):
        """更新尺寸"""
        if x_open is not None:
            self.x_open = float(x_open)
        if y_open is not None:
            self.y_open = float(y_open)
        self.mark_as_modified()
    
    def update_info(self, pad_name=None, net_name=None, bonding=None):
        """更新pad信息"""
        if pad_name is not None:
            self.pad_name = pad_name
        if net_name is not None:
            self.net_name = net_name
        if bonding is not None:
            self.bonding = bonding
        self.mark_as_modified()
    
    def clone(self):
        """创建pad的副本"""
        return Pad(
            self.pad_id,
            self.pad_name,
            self.x_coord,
            self.y_coord,
            self.x_open,
            self.y_open,
            self.net_name,
            self.bonding
        )
    
    def __repr__(self):
        return f"Pad(id={self.pad_id}, name={self.pad_name}, coords=({self.x_coord}, {self.y_coord}), open=({self.x_open}, {self.y_open}), net={self.net_name}, bonding={self.bonding})"
    
    def to_dict(self):
        return {
            'pad_id': self.pad_id,
            'pad_name': self.pad_name,
            'x_coord': self.x_coord,
            'y_coord': self.y_coord,
            'x_open': self.x_open,
            'y_open': self.y_open,
            'net_name': self.net_name,
            'bonding': self.bonding,
            'is_modified': self._modified,
            'is_marked_for_deletion': self._marked_for_deletion
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建Pad对象"""
        pad = cls(
            data.get('pad_id', ''),
            data.get('pad_name', ''),
            data.get('x_coord', 0.0),
            data.get('y_coord', 0.0),
            data.get('x_open', 0.0),
            data.get('y_open', 0.0),
            data.get('net_name', ''),
            data.get('bonding', '')
        )
        # 恢复状态标记
        if data.get('is_modified', False):
            pad._modified = True
        if data.get('is_marked_for_deletion', False):
            pad._marked_for_deletion = True
        return pad
