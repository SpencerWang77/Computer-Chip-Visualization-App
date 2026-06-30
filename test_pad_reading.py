from data_handlers import ExcelHandler
from models import Pad


def test_pad_reading():
    handler = ExcelHandler()
    
    excel_file = "封装连线示意.xlsx"
    
    if handler.read_excel(excel_file):
        handler.print_pads_sample(10)
        
        pads = handler.get_pads()
        print(f"\nSample pad dict (first pad):")
        print(pads[0].to_dict() if pads else "No pads found")
    else:
        print("Failed to read Excel file")


if __name__ == "__main__":
    test_pad_reading()
