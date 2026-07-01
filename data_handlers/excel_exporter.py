import openpyxl
from datetime import datetime
import os


class ExcelExporter:
    def __init__(self):
        self.template_file = "封装连线示意.xlsx"
    
    def export_modified_data(self, pads, output_path=None):
        """导出修改后的pads数据到新的Excel文件"""
        try:
            from datetime import datetime
            
            if output_path is None:
                # 默认导出到exports子文件夹
                if not os.path.exists("exports"):
                    os.makedirs("exports")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"modified_pads_{timestamp}.xlsx"
                output_path = os.path.join("exports", output_filename)
            
            # 获取文件名和目录
            output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else "."
            output_filename = os.path.basename(output_path)
            
            # 加载原始Excel文件作为模板（不修改原始文件）
            source_sheet = None
            
            if os.path.exists(self.template_file):
                source_workbook = openpyxl.load_workbook(self.template_file)
                if "connect" in source_workbook.sheetnames:
                    source_sheet = source_workbook["connect"]
            
            # 创建新的工作簿
            workbook = openpyxl.Workbook()
            connect_sheet = workbook.active
            connect_sheet.title = "connect"
            
            if source_sheet:
                # 复制标题和说明行
                for row in source_sheet.iter_rows(min_row=1, max_row=2):
                    for cell in row:
                        connect_sheet.cell(row=cell.row, column=cell.column, value=cell.value)
            else:
                # 创建默认标题行
                headers = ["Die Pad No", "Pad name", "X-coord", "Y-coord", "X open", "Y open", "Net Name", "Bonding", "", "Remark"]
                for i, header in enumerate(headers, 1):
                    connect_sheet.cell(row=1, column=i, value=header)
                
                # 创建单位说明行
                units = ["", "", "(after shrink)", "(after shrink)", "(after shrink)", "(after shrink)", "", "relationship", "", ""]
                for i, unit in enumerate(units, 1):
                    connect_sheet.cell(row=2, column=i, value=unit)
            
            # 写入修改后的pad数据
            for i, pad in enumerate(pads, 3):  # 从第3行开始
                connect_sheet.cell(row=i, column=1, value=pad.pad_id)
                connect_sheet.cell(row=i, column=2, value=pad.pad_name)
                connect_sheet.cell(row=i, column=3, value=pad.x_coord)
                connect_sheet.cell(row=i, column=4, value=pad.y_coord)
                connect_sheet.cell(row=i, column=5, value=pad.x_open)
                connect_sheet.cell(row=i, column=6, value=pad.y_open)
                connect_sheet.cell(row=i, column=7, value=pad.net_name)
                connect_sheet.cell(row=i, column=8, value=pad.bonding)
                connect_sheet.cell(row=i, column=9, value="")
                connect_sheet.cell(row=i, column=10, value="")
            
            # 确保exports文件夹存在
            if not os.path.exists("exports"):
                os.makedirs("exports")
            
            # 将文件保存到exports子文件夹
            output_path = os.path.join("exports", output_filename)
            
            # 保存新的Excel文件
            workbook.save(output_path)
            return True, output_path
            
        except Exception as e:
            print(f"Excel export failed: {e}")
            return False, None
    
    def get_export_summary(self, pads):
        """获取导出统计信息"""
        total_pads = len(pads)
        modified_pads = len([p for p in pads if p.is_modified])
        
        return {
            'total_pads': total_pads,
            'modified_pads': modified_pads,
            'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
