import re
from typing import List

import openpyxl

from models import Pad

# Matches bonding values like "LF.119", "LF 12", "LF_7"
_LF_PATTERN = re.compile(r'^LF[._\s]*(\d+)$', re.IGNORECASE)


class ExcelHandler:
    """Reads pad data from the 'connect' sheet of a bonding-diagram workbook.

    Expected sheet layout:
      row 1: headers (Die Pad No, Pad name, X-coord, Y-coord, X open, Y open,
             Net Name, Bonding, ...)
      row 2: units / remarks
      row 3+: pad data
    """

    def __init__(self):
        self.pads: List[Pad] = []
        self.source_file = None

    def read_excel(self, file_path: str) -> bool:
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)

            if 'connect' not in workbook.sheetnames:
                raise ValueError("Missing 'connect' worksheet")

            connect_sheet = workbook['connect']

            self.pads = []
            for row in connect_sheet.iter_rows(min_row=3, max_row=connect_sheet.max_row):
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

                self.pads.append(Pad(pad_id, pad_name, x_coord, y_coord,
                                     x_open, y_open, net_name, bonding))

            self.source_file = file_path
            return True

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return False

    def get_pads(self) -> List[Pad]:
        return self.pads

    def get_max_lf_pin(self) -> int:
        """Highest lead frame pin number referenced by any pad's bonding.

        Returns 0 when no LF.<n> bonding exists.
        """
        max_pin = 0
        for pad in self.pads:
            match = _LF_PATTERN.match(pad.bonding)
            if match:
                max_pin = max(max_pin, int(match.group(1)))
        return max_pin

    def suggest_pin_count(self) -> int:
        """Pin count suggestion: highest LF.<n> rounded up to a multiple of 4."""
        max_pin = self.get_max_lf_pin()
        if max_pin == 0:
            return 0
        return ((max_pin + 3) // 4) * 4
