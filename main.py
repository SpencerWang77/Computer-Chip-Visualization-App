import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QFileDialog, QSpacerItem, QSizePolicy, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont
from ui import UploadSection, FormatDescription, ProgressControl, VisualizationWindow
from data_handlers import ExcelHandler, ExcelExporter


class ChipVisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.excel_handler = ExcelHandler()
        self.current_file = None
        self.progress_control = ProgressControl()
        self.visualization_windows = []  # 保持可视化窗口的引用
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("芯片连线可视化")
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()  # 默认全屏显示
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        title_label = QLabel("芯片连线可视化系统")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 24, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        self.upload_section = UploadSection()
        self.upload_section.get_upload_button().clicked.connect(self.open_file_dialog)
        main_layout.addWidget(self.upload_section)
        
        format_description = FormatDescription()
        main_layout.addWidget(format_description)
        
        status_label = self.progress_control.create_status_label()
        self.progress_control.hide_status_label()
        main_layout.addWidget(status_label)
        
        start_button = self.progress_control.create_start_button()
        start_button.clicked.connect(self.start_visualization)
        self.progress_control.hide_start_button()
        main_layout.addWidget(start_button, 0, Qt.AlignCenter)
        
        # 保存按钮引用以便调试
        self.start_button = start_button
        
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            file_name = os.path.basename(file_path)
            
            for widget in self.findChildren(UploadSection):
                widget.set_file_selected(file_name)
            
            self.progress_control.show_start_button()
            self.progress_control.show_status_label()
            self.read_excel_file()
    
    def read_excel_file(self):
        self.progress_control.set_loading_status()
        self.progress_control.disable_start_button()
        
        if self.excel_handler.read_excel(self.current_file):
            print("Excel file loaded successfully!")
            pads = self.excel_handler.get_pads()
            print(f"Total pads: {len(pads)}")
            
            self.progress_control.set_success_status()
            self.progress_control.enable_start_button()
        else:
            print("Failed to load Excel file")
            if self.progress_control.status_label:
                self.progress_control.status_label.setText("文件读取失败，请重新选择")
    
    def start_visualization(self):
        if self.current_file:
            print("=== start_visualization called ===")
            
            # 检查按钮状态
            if hasattr(self, 'start_button'):
                print(f"Button enabled: {self.start_button.isEnabled()}")
                print(f"Button visible: {self.start_button.isVisible()}")
            
            # 检查当前文件
            if self.current_file:
                print(f"Current file: {self.current_file}")
            else:
                print("ERROR: No current file set")
                return
            
            # 检查Excel handler
            if not hasattr(self.excel_handler, 'get_pads'):
                print("ERROR: Excel handler has no get_pads method")
                return
                
            # 获取pads
            pads = self.excel_handler.get_pads()
            print(f"Got {len(pads)} from handler")
            
            # 获取框架参数
            frame_params = self.upload_section.get_frame_parameters()
            print(f"Frame parameters: {frame_params}")
            
            if pads:
                # 启动增强版编辑器
                from chip_editor_app import ChipEditorApp
                enhanced_viz = ChipEditorApp()
                enhanced_viz.pads = pads  # 直接设置pads
                
                # 设置场景并传递框架参数
                enhanced_viz.scene.set_pads(pads, frame_params)  # 传递框架参数
                
                enhanced_viz.export_btn.setEnabled(True)
                enhanced_viz.status_label.setText(f"已加载 {len(pads)} 个Pad | 点击Pad进行编辑，可修改: Pad名称、网络名称、焊接关系")
                enhanced_viz.show()
                enhanced_viz.showMaximized()  # 默认全屏显示
                
                # 自动缩放到整个LF框架区域
                if frame_params:
                    enhanced_viz.view.fit_in_view()
                
                print("Enhanced visualization started")
            else:
                print("No pads available for visualization")
            return
            
        # 检查pads内容
        if len(pads) > 0:
            print(f"First pad: {pads[0]}")
        
        # 创建可视化窗口
        try:
            print(f"Creating VisualizationWindow with {len(pads)} pads")
            viz_window = VisualizationWindow(pads)
            print(f"VisualizationWindow created, calling show()")
            
            # 保持对窗口的引用，防止被垃圾回收
            self.visualization_windows.append(viz_window)
            
            # 确保窗口被正确显示
            viz_window.show()
            viz_window.raise_()
            viz_window.activateWindow()
            
            print(f"show() called successfully - visualization window should be visible {len(self.visualization_windows)}")
        except Exception as e:
            print(f"ERROR creating visualization window: {e}")
            import traceback
            traceback.print_exc()
    
    def test_button_function(self):
        print("Test button clicked - button connection is working")
        print(f"Current file: {self.current_file}")
        print(f"Has Excel handler: {hasattr(self.excel_handler, 'get_pads')}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(244, 247, 250))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.Button, QColor(236, 240, 241))
    palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(52, 152, 219))
    palette.setColor(QPalette.Highlight, QColor(41, 128, 185))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = ChipVisApp()
    window.show()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
