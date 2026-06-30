import sys
from PyQt5.QtWidgets import QApplication
from data_handlers import ExcelHandler

def test_scene_creation():
    print("Testing scene creation with text items...")
    
    app = QApplication([])
    app.setStyle('Fusion')
    
    try:
        # 导入可视化窗口
        from ui import VisualizationWindow
        
        # 加载数据
        handler = ExcelHandler()
        if not handler.read_excel("封装连线示意.xlsx"):
            print("FAILED: Could not read Excel file")
            return
        
        pads = handler.get_pads()
        print(f"Loaded {len(pads)} pads")
        
        # 创建可视化窗口
        viz_window = VisualizationWindow(pads)
        
        # 检查场景中的项目
        scene = viz_window.scene
        print(f"Scene has {len(scene.items())} items")
        
        # 检查前几个pad项目
        count = 0
        text_count = 0
        rect_count = 0
        
        for item in scene.items():
            from ui.chip_visualization import PadGraphicsItem
            if isinstance(item, PadGraphicsItem):
                rect_count += 1
                if hasattr(item, 'text_item') and item.text_item:
                    text_count += 1
                    if count < 3:
                        debug_info = item.get_debug_info()
                        print(f"\nPad {count+1}: {debug_info.get('pad_id', 'unknown')}")
                        print(f"  SOC number: {debug_info.get('pad_number', 'unknown')}")
                        print(f"  Text position: {debug_info.get('text_pos', 'unknown')}")
                        print(f"  Font size: {debug_info.get('font_size', 'unknown')}")
                count += 1
                
                if count >= 5:
                    break
        
        print(f"\nFound {rect_count} pad items")
        print(f"Found {text_count} text items")
        
        if text_count > 0:
            print("\nSUCCESS: Text items are being created!")
        else:
            print("\nFAILED: No text items found!")
        
        viz_window.show()
        app.exec_()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scene_creation()
