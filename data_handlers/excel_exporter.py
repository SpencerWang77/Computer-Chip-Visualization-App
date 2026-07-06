import os
from datetime import datetime

import openpyxl


class ExcelExporter:
    """Writes the (possibly modified) pad data to a new Excel file.

    The original workbook is never modified; the caller chooses the output
    path. Multi-die exports go into one combined sheet whose coordinates are
    in the shared ring coordinate system (origin at the ring's bottom-left).
    """

    def __init__(self, source_file=None):
        self.source_file = source_file

    def export_combined(self, rows, output_path):
        """Export a combined sheet of all pads across every die.

        `rows` is a list of (die_name, Pad) with coordinates already in the
        ring frame. Returns (success, saved_path).
        """
        try:
            if not output_path:
                raise ValueError("No output path given")
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "All Pads"

            headers = ["Die", "Die Pad No", "Pad name", "X-coord (ring)",
                       "Y-coord (ring)", "X open", "Y open", "Net Name", "Bonding"]
            units = ["", "", "", "(ring frame)", "(ring frame)",
                     "(after rotation)", "(after rotation)", "", "relationship"]
            for col, value in enumerate(headers, 1):
                sheet.cell(row=1, column=col, value=value)
            for col, value in enumerate(units, 1):
                sheet.cell(row=2, column=col, value=value)

            for row_idx, (die_name, pad) in enumerate(rows, 3):
                sheet.cell(row=row_idx, column=1, value=die_name)
                sheet.cell(row=row_idx, column=2, value=pad.pad_id)
                sheet.cell(row=row_idx, column=3, value=pad.pad_name)
                sheet.cell(row=row_idx, column=4, value=pad.x_coord)
                sheet.cell(row=row_idx, column=5, value=pad.y_coord)
                sheet.cell(row=row_idx, column=6, value=pad.x_open)
                sheet.cell(row=row_idx, column=7, value=pad.y_open)
                sheet.cell(row=row_idx, column=8, value=pad.net_name)
                sheet.cell(row=row_idx, column=9, value=pad.bonding)

            workbook.save(output_path)
            return True, output_path

        except Exception as e:
            print(f"Excel export failed: {e}")
            return False, None

    def get_export_summary(self, pads):
        return {
            'total_pads': len(pads),
            'modified_pads': len([p for p in pads if p.is_modified]),
            'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
