from data_handlers import ExcelHandler
from models import ChipLayout


def test_chip_layout():
    handler = ExcelHandler()
    excel_file = "封装连线示意.xlsx"
    
    if handler.read_excel(excel_file):
        pads = handler.get_pads()
        print(f"Successfully loaded {len(pads)} pads")
        
        chip_layout = ChipLayout()
        chip_layout.set_pads(pads)
        
        coords_info = chip_layout.get_expanded_coordinates()
        print(f"\nChip Layout Information:")
        print(f"X range: {coords_info['min_x']:.2f} to {coords_info['max_x']:.2f}")
        print(f"Y range: {coords_info['min_y']:.2f} to {coords_info['max_y']:.2f}")
        print(f"Total size: {coords_info['width']:.2f} × {coords_info['height']:.2f}")
        
        print(f"\nSample Pad Information (first 5):")
        print("=" * 80)
        for i, pad in enumerate(pads[:5], 1):
            rect_info = chip_layout.get_pad_rectangle(pad.pad_id)
            x1, y1, x2, y2 = rect_info
            print(f"{i}. Pad {pad.pad_id} ({pad.pad_name})")
            print(f"   Center: ({pad.x_coord:.4f}, {pad.y_coord:.4f})")
            print(f"   Size: {pad.x_open:.2f} × {pad.y_open:.2f}")
            print(f"   Rectangle: ({x1:.4f}, {y1:.4f}) to ({x2:.4f}, {y2:.4f})")
            print(f"   Net: {pad.net_name}, Bonding: {pad.bonding}")
            print()
        
        return True
    else:
        print("Failed to read Excel file")
        return False


if __name__ == "__main__":
    test_chip_layout()