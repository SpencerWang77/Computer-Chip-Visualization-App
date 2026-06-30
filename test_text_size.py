from data_handlers import ExcelHandler
from models import Pad

def test_text_size():
    handler = ExcelHandler()
    excel_file = "封装连线示意.xlsx"
    
    if handler.read_excel(excel_file):
        pads = handler.get_pads()
        print(f"Loaded {len(pads)} pads")
        
        print("\nAnalyzing pad sizes for text display:")
        print("=" * 80)
        
        for i, pad in enumerate(pads[:10], 1):
            min_dim = min(pad.x_open, pad.y_open)
            suggested_font = max(10, int(min_dim / 3))
            
            print(f"{i}. Pad {pad.pad_id}:")
            print(f"   Size: {pad.x_open:.2f} x {pad.y_open:.2f}")
            print(f"   Min dimension: {min_dim:.2f}")
            print(f"   Suggested font size: {suggested_font}")
            print(f"   Text to display: {pad.pad_id.split('.')[-1]}")
            print()
        
        print(f"\nSmallest pad size: {min(p.x_open for p in pads):.2f} x {min(p.y_open for p in pads):.2f}")
        print(f"Largest pad size: {max(p.x_open for p in pads):.2f} x {max(p.y_open for p in pads):.2f}")
    else:
        print("Failed to load Excel file")

if __name__ == "__main__":
    test_text_size()
