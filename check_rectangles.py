from data_handlers import ExcelHandler
from models import ChipLayout

handler = ExcelHandler()
handler.read_excel("封装连线示意.xlsx")
pads = handler.get_pads()

chip_layout = ChipLayout()
chip_layout.set_pads(pads)

print("Checking rectangle calculations:")
print("="*60)

for i, pad in enumerate(pads[:5], 1):
    rect = chip_layout.get_pad_rectangle(pad.pad_id)
    print(f"\n{i}. Pad {pad.pad_id}:")
    print(f"   Expected center: ({pad.x_coord}, {pad.y_coord})")
    print(f"   Expected size: {pad.x_open} x {pad.y_open}")
    
    if rect:
        x1, y1, x2, y2 = rect
        actual_width = x2 - x1
        actual_height = y2 - y1
        calculated_center_x = (x1 + x2) / 2
        calculated_center_y = (y1 + y2) / 2
        
        print(f"   Rectangle: ({x1:.2f}, {y1:.2f}) to ({x2:.2f}, {y2:.2f})")
        print(f"   Actual size: {actual_width:.2f} x {actual_height:.2f}")
        print(f"   Calculated center: ({calculated_center_x:.2f}, {calculated_center_y:.2f})")
        
        # 检查矩形信息
        print(f"   Text should be centered at: ({pad.x_coord - x1 + (pad.x_open/2 - actual_width/2):.2f}, {pad.y_coord - y1 + (pad.y_open/2 - actual_height/2):.2f})")
