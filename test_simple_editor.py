from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from models import Pad

class SimplePadEditor(QWidget):
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pad = None
        self.original_data = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 只读字段
        self.pad_id_label = QLabel("Pad ID: -")
        self.pad_id_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.pad_id_label)
        
        self.coord_label = QLabel("坐标: -")
        layout.addWidget(self.coord_label)
        
        self.size_label = QLabel("尺寸: -")
        layout.addWidget(self.size_label)
        
        # 可编辑字段
        layout.addWidget(QLabel("Pad Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 4px; padding: 5px;")
        layout.addWidget(self.name_edit)
        
        layout.addWidget(QLabel("Net Name:"))
        self.net_edit = QLineEdit()
        self.net_edit.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 4px; padding: 5px;")
        layout.addWidget(self.net_edit)
        
        layout.addWidget(QLabel("Bonding Relationship:"))
        self.bonding_edit = QLineEdit()
        self.bonding_edit.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 4px; padding: 5px;")
        layout.addWidget(self.bonding_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 8px 16px;")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 16px;")
        self.save_btn.clicked.connect(self.save_changes)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_pad(self, pad):
        self.current_pad = pad
        self.original_data = {
            'pad_name': pad.pad_name,
            'net_name': pad.net_name,
            'bonding': pad.bonding
        }
        
        self.pad_id_label.setText(f"Pad ID: {pad.pad_id}")
        self.coord_label.setText(f"坐标: ({pad.x_coord:.4f}, {pad.y_coord:.4f})")
        self.size_label.setText(f"尺寸: {pad.x_open:.2f} × {pad.y_open:.2f}")
        
        self.name_edit.setText(pad.pad_name)
        self.net_edit.setText(pad.net_name)
        self.bonding_edit.setText(pad.bonding)
    
    def cancel_changes(self):
        if self.current_pad and self.original_data:
            self.name_edit.setText(self.original_data['pad_name'])
            self.net_edit.setText(self.original_data['net_name'])
            self.bonding_edit.setText(self.original_data['bonding'])
    
    def save_changes(self):
        if self.current_pad:
            # 更新pad数据
            self.current_pad.update_info(
                pad_name=self.name_edit.text(),
                net_name=self.net_edit.text(),
                bonding=self.bonding_edit.text()
            )
            
            QMessageBox.information(self, "保存成功", f"Pad {self.current_pad.pad_id} 的修改已保存！")
            self.data_changed.emit()

def test_simple_editor():
    app = QApplication([])
    
    # 创建测试pad
    test_pad = Pad("SOC.1", "VCCA1", 100.0, 100.0, 50.0, 50.0, "VCC", "bond1")
    
    editor = SimplePadEditor()
    editor.load_pad(test_pad)
    editor.show()
    
    app.exec_()

if __name__ == "__main__":
    test_simple_editor()
