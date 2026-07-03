import os
from datetime import datetime

import openpyxl


class ExcelExporter:
    """Writes the (possibly modified) pad list to a new Excel file.

    The original workbook is never modified. When a source file is given,
    its two header rows are copied so the exported file keeps the same
    format as the input.
    """

    DEFAULT_EXPORT_DIR = "exports"

    def __init__(self, source_file=None):
        self.source_file = source_file

    def export_modified_data(self, pads, output_path=None):
        """Export pads to output_path (or a timestamped file in exports/).

        Returns (success, saved_path).
        """
        try:
            if output_path is None:
                os.makedirs(self.DEFAULT_EXPORT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.DEFAULT_EXPORT_DIR,
                                           f"modified_pads_{timestamp}.xlsx")
            else:
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

            workbook = openpyxl.Workbook()
            connect_sheet = workbook.active
            connect_sheet.title = "connect"

            header_rows = self._read_source_header_rows()
            if header_rows:
                for row_idx, row_values in enumerate(header_rows, 1):
                    for col_idx, value in enumerate(row_values, 1):
                        connect_sheet.cell(row=row_idx, column=col_idx, value=value)
            else:
                headers = ["Die Pad No", "Pad name", "X-coord", "Y-coord",
                           "X open", "Y open", "Net Name", "Bonding", "", "Remark"]
                units = ["", "", "(after shrink)", "(after shrink)",
                         "(after shrink)", "(after shrink)", "", "relationship", "", ""]
                for col_idx, value in enumerate(headers, 1):
                    connect_sheet.cell(row=1, column=col_idx, value=value)
                for col_idx, value in enumerate(units, 1):
                    connect_sheet.cell(row=2, column=col_idx, value=value)

            for row_idx, pad in enumerate(pads, 3):
                connect_sheet.cell(row=row_idx, column=1, value=pad.pad_id)
                connect_sheet.cell(row=row_idx, column=2, value=pad.pad_name)
                connect_sheet.cell(row=row_idx, column=3, value=pad.x_coord)
                connect_sheet.cell(row=row_idx, column=4, value=pad.y_coord)
                connect_sheet.cell(row=row_idx, column=5, value=pad.x_open)
                connect_sheet.cell(row=row_idx, column=6, value=pad.y_open)
                connect_sheet.cell(row=row_idx, column=7, value=pad.net_name)
                connect_sheet.cell(row=row_idx, column=8, value=pad.bonding)

            workbook.save(output_path)
            return True, output_path

        except Exception as e:
            print(f"Excel export failed: {e}")
            return False, None

    def _read_source_header_rows(self):
        """First two rows of the source 'connect' sheet, or None."""
        if not self.source_file or not os.path.exists(self.source_file):
            return None
        try:
            workbook = openpyxl.load_workbook(self.source_file, read_only=True)
            if "connect" not in workbook.sheetnames:
                return None
            sheet = workbook["connect"]
            rows = []
            for row in sheet.iter_rows(min_row=1, max_row=2, values_only=True):
                rows.append(list(row))
            return rows
        except Exception:
            return None

    def get_export_summary(self, pads):
        return {
            'total_pads': len(pads),
            'modified_pads': len([p for p in pads if p.is_modified]),
            'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
