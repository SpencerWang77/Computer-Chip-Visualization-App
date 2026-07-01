from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

def test_file_dialog():
    app = QApplication([])
    app.setStyle('Fusion')
    
    # 测试文件对话框
    print("Opening file dialog...")
    
    dialog = QFileDialog()
    dialog.setDirectory(os.getcwd())
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter("Excel files (*.xlsx *.xls);;All files (*.*)")
    dialog.setWindowTitle("选择导出路径")
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    dialog.selectFile("test_export.xlsx")
    
    print(f"Dialog mode: {dialog.fileMode()}")
    print(f"Accept mode: {dialog.acceptMode()}")
    
    result = dialog.exec_()
    print(f"Dialog result: {result}")
    
    if result == QFileDialog.Accepted:
        selected = dialog.selectedFiles()
        if selected:
            print(f"Selected path: {selected[0]}")
            QMessageBox.information(None, "测试", f"选择的路径: {selected[0]}")
        else:
            print("No file selected")
    else:
        print("User cancelled")

import os

test_file_dialog()
