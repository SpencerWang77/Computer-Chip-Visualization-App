import sys

def test_imports():
    print("Starting import test...")
    
    try:
        print("1. Importing PyQt5...")
        from PyQt5.QtWidgets import QApplication
        print("   OK PyQt5 imported")
    except Exception as e:
        print(f"   FAILED PyQt5 import failed: {e}")
        return
    
    try:
        print("2. Creating QApplication...")
        app = QApplication([])
        print("   OK QApplication created")
    except Exception as e:
        print(f"   FAILED QApplication creation failed: {e}")
        return
    
    try:
        print("3. Importing models...")
        from models import Pad
        print("   OK Models imported")
    except Exception as e:
        print(f"   FAILED Models import failed: {e}")
        return
    
    try:
        print("4. Importing data handlers...")
        from data_handlers import ExcelHandler
        print("   OK Data handlers imported")
    except Exception as e:
        print(f"   FAILED Data handlers import failed: {e}")
        return
    
    try:
        print("5. Importing UI components...")
        from ui import VisualizationWindow
        print("   OK UI components imported")
    except Exception as e:
        print(f"   FAILED UI components import failed: {e}")
        return
    
    try:
        print("6. Loading Excel data...")
        handler = ExcelHandler()
        if handler.read_excel("封装连线示意.xlsx"):
            pads = handler.get_pads()
            print(f"   OK Loaded {len(pads)} pads")
        else:
            print("   FAILED Failed to load Excel")
            return
    except Exception as e:
        print(f"   FAILED Excel loading failed: {e}")
        return
    
    try:
        print("7. Creating VisualizationWindow...")
        viz_window = VisualizationWindow(pads)
        print("   OK VisualizationWindow created")
        
        print("8. Showing window...")
        viz_window.show()
        print("   OK Window shown")
        
        print("\nAll tests passed! Window should be visible.")
        app.exec_()
    except Exception as e:
        print(f"   FAILED Window creation/show failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports()
