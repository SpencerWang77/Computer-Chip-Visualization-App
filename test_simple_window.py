import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

def main():
    print("Step 1: Creating QApplication...")
    app = QApplication(sys.argv)
    
    print("Step 2: Creating QMainWindow...")
    window = QMainWindow()
    window.setWindowTitle("Test Window")
    window.setGeometry(100, 100, 400, 300)
    
    print("Step 3: Setting central widget...")
    central = QWidget()
    layout = QVBoxLayout()
    label = QLabel("Hello from PyQt5!")
    layout.addWidget(label)
    central.setLayout(layout)
    window.setCentralWidget(central)
    
    print("Step 4: Showing window...")
    window.show()
    
    print("Step 5: Starting event loop (will run until window is closed)...")
    print("Close the window to continue...")
    
    # 返回而不是退出
    result = app.exec_()
    print(f"Event loop finished with result: {result}")
    return result

if __name__ == "__main__":
    main()
