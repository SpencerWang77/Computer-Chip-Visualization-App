import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

def main():
    print("Starting PyQt5 test...")
    app = QApplication(sys.argv)
    print("QApplication created")
    
    msg = QMessageBox()
    msg.setWindowTitle("Test")
    msg.setText("If you see this, PyQt5 is working!")
    msg.setIcon(QMessageBox.Information)
    print("Showing message box...")
    result = msg.exec_()
    print(f"Message box closed with result: {result}")

if __name__ == "__main__":
    main()
