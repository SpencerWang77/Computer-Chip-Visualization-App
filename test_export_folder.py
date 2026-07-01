from data_handlers import ExcelExporter, ExcelHandler
import os

handler = ExcelHandler()
handler.read_excel('封装连线示意.xlsx')
pads = handler.get_pads()
exporter = ExcelExporter()
success, filename = exporter.export_modified_data(pads)
print(f'Export result: {success}, file: {filename}')
if success:
    print(f'File exists in exports/: {os.path.exists(os.path.join("exports", filename))}')
    print(f'Full path: exports/{filename}')
