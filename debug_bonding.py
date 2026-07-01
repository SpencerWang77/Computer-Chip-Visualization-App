import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from data_handlers import ExcelHandler

# 读取Excel文件
handler = ExcelHandler()

# 查找Excel文件
import glob
excel_files = glob.glob("*.xlsx")
if excel_files:
    file_path = excel_files[0]
    print(f"使用Excel文件: {file_path}")
else:
    print("没有找到Excel文件")
    sys.exit(1)

if handler.read_excel(file_path):
    pads = handler.get_pads()
    print(f"Total pads: {len(pads)}")
    
    # 统计bonding关系
    bonding_stats = {}
    lf_pads = {}
    
    for pad in pads:
        bonding = pad.bonding if hasattr(pad, 'bonding') else ""
        bonding_upper = bonding.upper()
        
        if bonding_upper in bonding_stats:
            bonding_stats[bonding_upper] += 1
        else:
            bonding_stats[bonding_upper] = 1
        
        # 收集LF相关的pad
        if "LF" in bonding_upper:
            # 提取LF的唯一标识符（匹配LF.10格式）
            import re
            match = re.search(r'LF[._\s]*([A-Z0-9]+)', bonding_upper)
            lf_key = f"LF_{match.group(1)}" if match else "LF_DEFAULT"
            
            if lf_key not in lf_pads:
                lf_pads[lf_key] = []
            lf_pads[lf_key].append(pad.pad_id)
    
    print("\n=== Bonding关系统计 ===")
    for bonding, count in sorted(bonding_stats.items()):
        if count > 0:
            print(f"{bonding}: {count}个pads")
    
    print("\n=== LF类型pads统计 ===")
    for lf_key, pad_ids in lf_pads.items():
        print(f"{lf_key}: {len(pad_ids)}个pads")
        print(f"  示例: {pad_ids[:3]}...")  # 显示前3个
    
    print(f"\n总共找到{len(lf_pads)}种不同的LF类型")
else:
    print("无法读取Excel文件")