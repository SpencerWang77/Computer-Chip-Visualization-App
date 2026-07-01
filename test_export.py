from data_handlers import ExcelHandler, ExcelExporter
from models import Pad

def test_excel_export():
    print("Testing Excel export functionality...")
    
    # 加载原始数据
    handler = ExcelHandler()
    if not handler.read_excel("封装连线示意.xlsx"):
        print("FAILED: Could not read source file")
        return
    
    pads = handler.get_pads()
    print(f"Loaded {len(pads)} pads from source file")
    
    # 模拟一些修改
    pads[0].update_info(pad_name="MODIFIED_VCCA1", net_name="MODIFIED_VCC")
    pads[1].update_info(bonding="NEW_BONDING")
    
    # 检查修改状态
    modified = [p for p in pads if p.is_modified]
    print(f"Modified pads: {len(modified)}")
    for pad in modified[:3]:
        print(f"  - {pad.pad_id}: {pad.pad_name}")
    
    # 测试导出
    exporter = ExcelExporter()
    success, filename = exporter.export_modified_data(pads)
    
    if success:
        print(f"SUCCESS: Exported to {filename}")
        
        # 获取导出统计
        summary = exporter.get_export_summary(pads)
        print(f"Export summary: {summary}")
    else:
        print("FAILED: Export failed")

if __name__ == "__main__":
    test_excel_export()
