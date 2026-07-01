import sys
from PyQt5.QtWidgets import QApplication
from data_handlers import ExcelHandler

def debug_visibility():
    print("Starting visibility debug...")
    
    app = QApplication([])
    
    # 加载数据
    handler = ExcelHandler()
    if not handler.read_excel("封装连线示意.xlsx"):
        print("FAILED: Could not read Excel file")
        return
    
    pads = handler.get_pads()
    print(f"Loaded {len(pads)} pads")
    
    # 检查前几个pad的状态
    from models import ChipLayout
    chip_layout = ChipLayout()
    
    print("Checking pad states before layout calculation:")
    for i, pad in enumerate(pads[:5]):
        print(f"  Pad {i+1}: {pad.pad_id}")
        print(f"    is_modified: {pad.is_modified if hasattr(pad, 'is_modified') else 'N/A'}")
        print(f"    is_marked_for_deletion: {pad.is_marked_for_deletion() if hasattr(pad, 'is_marked_for_deletion') else 'N/A'}")
        print(f"    coords: ({pad.x_coord}, {pad.y_coord}), size: ({pad.x_open}, {pad.y_open})")
    
    # 测试set_pads方法
    print("\nTesting set_pads method...")
    chip_layout.set_pads(pads)
    
    remaining_pads = chip_layout.get_all_pads()
    print(f"Pads after set_pads: {len(remaining_pads)}")
    
    # 检查布局计算
    print("\nChecking layout calculations:")
    for i, pad in enumerate(pads[:3]):
        rect = chip_layout.get_pad_rectangle(pad.pad_id)
        print(f"  Pad {pad.pad_id}: rectangle = {rect}")
    
    # 测试导入可视化组件
    print("\nTesting visualization components import...")
    try:
        from ui import VisualizationWindow
        print("  OK - VisualizationWindow imported")
        
        # 创建可视化窗口
        print("Creating VisualizationWindow...")
        viz_window = VisualizationWindow(pads)
        print("  OK - VisualizationWindow created")
        
        # 检查场景
        print(f"Scene items: {len(viz_window.scene.items())}")
        
        # 检查场景坐标
        scene_rect = viz_window.scene.sceneRect()
        print(f"Scene rectangle: ({scene_rect.x():.2f}, {scene_rect.y():.2f}) to ({scene_rect.width():.2f}, {scene_rect.height():.2f})")
        
        print("\nSUCCESS - All checks passed!")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    # sys.exit(app.exec_())

if __name__ == "__main__":
    debug_visibility()
