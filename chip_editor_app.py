import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QPushButton, QLabel, QMessageBox, QFileDialog, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from data_handlers import ExcelHandler, ExcelExporter
import test_simple_editor

class ChipEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pads = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("芯片Pad可视化编辑器")
        self.setGeometry(100, 100, 1600, 1000)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("芯片Pad可视化编辑器")
        title_font = QFont("Microsoft YaHei", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        
        load_btn = QPushButton("加载Excel文件")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        load_btn.clicked.connect(self.load_excel_file)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(load_btn)
        
        main_layout.addLayout(header_layout)
        
        # 主内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：可视化区域
        from ui.chip_visualization import ChipScene, ChipVisualizationView
        
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        
        self.scene = ChipScene()
        self.view = ChipVisualizationView(self.scene)
        
        viz_layout.addWidget(self.view)
        content_splitter.addWidget(viz_widget)
        
        # 右侧：编辑区域
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        
        # 标题
        edit_title = QLabel("Pad属性编辑")
        edit_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        edit_title.setStyleSheet("color: #2c3e50; padding: 10px;")
        edit_title.setAlignment(Qt.AlignCenter)
        edit_layout.addWidget(edit_title)
        
        # 编辑器
        self.editor = test_simple_editor.SimplePadEditor()
        edit_layout.addWidget(self.editor)
        
        # 导出按钮
        export_container = QWidget()
        export_layout = QHBoxLayout(export_container)
        export_layout.addStretch()
        
        self.export_btn = QPushButton("导出修改后的Excel")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_modified_excel_with_path)
        
        export_layout.addWidget(self.export_btn)
        edit_layout.addWidget(export_container)
        
        # 颜色规则说明
        legend_container = QWidget()
        legend_layout = QVBoxLayout(legend_container)
        legend_layout.setContentsMargins(10, 5, 10, 5)
        
        legend_title = QLabel("颜色规则:")
        legend_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        legend_title.setStyleSheet("color: #2c3e50; padding: 5px;")
        legend_layout.addWidget(legend_title)
        
        legend_text = QLabel("""
Not Bond: 黑色
E-pad/VSS_ring: 深蓝色
LF: 浅色(相同LF同色)
SOC/PSRAM/DDRA/DDRB/ROM: 深灰色
未定义: 深红色(请联系王泽源修改规则)
选中: 橙色边框(填充不变)""")
        legend_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                color: #2c3e50;
                font-size: 10px;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
        """)
        legend_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        legend_layout.addWidget(legend_text)
        
        edit_layout.addWidget(legend_container)
        
        content_splitter.addWidget(edit_widget)
        
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(content_splitter, 1)
        
        # 底部状态栏
        self.status_label = QLabel("请先加载Excel文件开始编辑")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px 15px;
                font-size: 11px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # 应用样式
        self.apply_modern_style()
        
        # 自定义场景点击处理
        self.scene.mousePressEvent = self.handle_scene_click
    
    def handle_scene_click(self, event):
        """处理场景点击事件"""
        pos = event.scenePos()
        items = self.scene.items(pos)
        
        from ui.chip_visualization import PadGraphicsItem
        for item in items:
            if isinstance(item, PadGraphicsItem):
                # 选中这个并显示在编辑器中
                self.editor.load_pad(item.pad)
                return
        
        # 调用原始方法
        from ui.chip_visualization import ChipScene
        ChipScene.mousePressEvent(self.scene, event)
    
    def load_excel_file(self):
        """加载Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel files (*.xlsx *.xls);;All files (*.*)"
        )
        
        if file_path:
            handler = ExcelHandler()
            if handler.read_excel(file_path):
                self.pads = handler.get_pads()
                self.scene.set_pads(self.pads)
                self.export_btn.setEnabled(True)
                self.status_label.setText(f"已加载 {len(self.pads)} 个Pad | 点击Pad进行编辑")
                QMessageBox.information(self, "加载成功", f"成功加载 {len(self.pads)} 个Pad!")
            else:
                QMessageBox.warning(self, "加载失败", "无法读取Excel文件")
    
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
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
        """)
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        self.setPalette(palette)
    
    def _get_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_modified_excel_with_path(self):
        """导出修改后的数据，允许用户选择路径"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            
            # 默认路径为exports文件夹
            default_path = os.path.join(os.getcwd(), "exports")
            
            # 创建文件保存对话框
            dialog = QFileDialog()
            dialog.setDirectory(default_path)
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setNameFilter("Excel files (*.xlsx *.xls);;All files (*.*)")
            dialog.setWindowTitle("选择导出路径")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.selectFile(f"modified_pads_{self._get_timestamp()}.xlsx")
            
            # 显示对话框
            result = dialog.exec_()
            
            if result == QFileDialog.Accepted:
                selected_files = dialog.selectedFiles()
                if selected_files:
                    output_path = selected_files[0]
                    
                    # 导出到用户选择的路径
                    exporter = ExcelExporter()
                    success, result_path = exporter.export_modified_data(self.pads, output_path)
                    
                    if success:
                        summary = exporter.get_export_summary(self.pads)
                        
                        # 简化路径显示
                        if len(result_path) > 50:
                            short_path = "..." + result_path[-47:]
                        else:
                            short_path = result_path
                        
                        message = f"""
导出成功！

保存位置: {result_path}
已修改的Pads: {summary['modified_pads']}/{summary['total_pads']}
导出时间: {summary['export_time']}

注意: 原始Excel文件未被修改，所有修改都保存在新文件中。
"""
                        QMessageBox.information(self, "导出成功", message)
                        
                        # 更新状态栏
                        self.status_label.setText(f"  已导出 {summary['modified_pads']}/{summary['total_pads']} 个修改的Pad | 保存位置: {short_path}  ")
                    else:
                        QMessageBox.warning(self, "导出失败", "无法导出Excel文件")
            else:
                # 用户取消，使用默认路径到exports文件夹
                self.export_modified_excel()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "导出错误", f"导出过程中出现错误: {str(e)}")
    
    def export_modified_excel(self):
        """导出修改后的数据（默认路径到exports文件夹）"""
        try:
            exporter = ExcelExporter()
            success, result_path = exporter.export_modified_data(self.pads)
            
            if success:
                summary = exporter.get_export_summary(self.pads)
                
                # 简化路径显示
                if len(result_path) > 50:
                    short_path = "..." + result_path[-47:]
                else:
                    short_path = result_path
                
                message = f"""
导出成功！

保存位置: {result_path}
已修改的Pads: {summary['modified_pads']}/{summary['total_pads']}
导出时间: {summary['export_time']}

注意: 原始Excel文件未被修改，所有修改都保存在新文件中。
"""
                QMessageBox.information(self, "导出成功", message)
                
                # 更新状态栏
                self.status_label.setText(f"  已导出 {summary['modified_pads']}/{summary['total_pads']} 个修改的Pad | 保存位置: {short_path}  ")
            else:
                QMessageBox.warning(self, "导出失败", "无法导出Excel文件")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "导出错误", f"导出过程中出现错误: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ChipEditorApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
