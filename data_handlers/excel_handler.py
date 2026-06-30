import openpyxl
from typing import List, Optional
from models import Pad


class ExcelHandler:
    def __init__(self):
        self.pads: List[Pad] = []
        self.worksheet_data = {}
    
    def read_excel(self, file_path: str) -> bool:
        try:
            workbook = openpyxl.load_workbook(file_path)
            
            if 'connect' not in workbook.sheetnames:
                raise ValueError("Missing 'connect' worksheet")
            
            connect_sheet = workbook['connect']
            
            self.pads = []
            for row_idx, row in enumerate(connect_sheet.iter_rows(min_row=3, max_row=connect_sheet.max_row), start=3):
                pad_id = row[0].value
                if not pad_id:
                    continue
                
                pad_name = row[1].value if len(row) > 1 else ""
                x_coord = row[2].value if len(row) > 2 else 0
                y_coord = row[3].value if len(row) > 3 else 0
                x_open = row[4].value if len(row) > 4 else 0
                y_open = row[5].value if len(row) > 5 else 0
                net_name = row[6].value if len(row) > 6 else ""
                bonding = row[7].value if len(row) > 7 else ""
                
                pad = Pad(pad_id, pad_name, x_coord, y_coord, x_open, y_open, net_name, bonding)
                self.pads.append(pad)
            
            return True
            
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return False
    
    def get_pads(self) -> List[Pad]:
        return self.pads
    
    def print_pads_sample(self, count: int = 10):
        print(f"Total pads loaded: {len(self.pads)}")
        print(f"\nFirst {min(count, len(self.pads))} pads:")
        print("=" * 100)
        for i, pad in enumerate(self.pads[:count], 1):
            print(f"{i}. {pad}")
        print("=" * 100)
