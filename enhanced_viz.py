import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import (QApplication, QSplitter, QHBoxLayout, QVBoxLayout, QWidget, 
                             QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from data_handlers import ExcelHandler, ExcelExporter
import test_simple_editor

class EnhancedVisualizationWindow(QWidget):
    def __init__(self, pads, parent=None):
        super().__init__(parent)
        self.pads = pads
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("芯片Pad可视化 - 增强版")
        self.setGeometry(100, 100, 1400, 900)
        
        main_layout = QHBoxLayout(self)
        
        # 左侧可视化区域（使用现有的组件）
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # 导入现有的可视化组件
        from ui.chip_visualization import ChipScene, ChipVisualizationView
        
        self.scene = ChipScene()
        self.scene.set_pads(self.pads)
        
        # 自定义点击处理
        self.scene.mousePressEvent = self.custom_scene_press
        
        self.view = ChipVisualizationView(self.scene)
        
        self.content_splitter.addWidget(self.view)
        
        # 右侧编辑器
        self.editor = test_simple_editor.SimplePadEditor()
        self.editor.setFixedWidth(350)
        self.content_splitter.addWidget(self.editor)
        
        self.content_splitter.setStretchFactor(0, 4)
        self.content_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.content_splitter)
        
        # 底部区域
        bottom_layout = QHBoxLayout()
        
        self.status_label = QLabel(f"共加载 {len(self.pads)} 个Pad | 操作说明: 点击Pad查看详情, 可编辑字段: Pad名称, 网络名称, 焊接关系")
        self.status_label.setStyleSheet("background-color: #ecf0f1; color: #7f8c8d; padding: 8px; border-radius: 5px; font-size: 11px;")
        bottom_layout.addWidget(self.status_label, 1)
        
        self.export_btn = QPushButton("导出修改后的Excel")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.export_btn.clicked.connect(self.export_modified_excel)
        bottom_layout.addWidget(self.export_btn)
        
        main_layout.addLayout(bottom_layout)
        
        self.apply_modern_style()
    
    def custom_scene_press(self, event):
        """自定义场景点击处理"""
        pos = event.scenePos()
        items = self.scene.items(pos)
        
        from ui.chip_visualization import PadGraphicsItem
        for item in items:
            if isinstance(item, PadGraphicsItem):
                # 选中这个pad，显示在编辑器中
                self.editor.load_pad(item.pad)
                return
        
        # 调用原始的方法
        from ui.chip_visualization import ChipScene
        ChipScene.mousePressEvent(self.scene, event)
    
    def export_modified_excel(self):
        """导出修改后的数据"""
        try:
            exporter = ExcelExporter()
            success, filename = exporter.export_modified_data(self.pads)
            
            if success:
                summary = exporter.get_export_summary(self.pads)
                message = f"""
导出成功！

文件名: {filename}
总pads: {summary['total_pads']}
修改的pads: {summary['modified_pads']}
导出时间: {summary['export_time']}
"""
                QMessageBox.information(self, "导出成功", message)
            else:
                QMessageBox.warning(self, "导出失败", "无法导出Excel文件")
                
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_modern_style(self):
        """应用现代化样式"""
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", Arial, sans-serif;
                background-color: #f5f6fa;
            }
        """)
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        self.setPalette(palette)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 加载数据
    handler = ExcelHandler()
    if not handler.read_excel("封装连线示意.xlsx"):
        QMessageBox.critical(None, "错误", "无法加载Excel文件")
        return
    
    pads = handler.get_pads()
    
    # 创建增强版窗口
    window = EnhancedVisualizationWindow(pads)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
