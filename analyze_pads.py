import openpyxl
import sys
import json

# 读取Excel文件
wb = openpyxl.load_workbook('封装连线示意.xlsx')
connect_sheet = wb['connect']

pads_data = []
for row_idx, row in enumerate(connect_sheet.iter_rows(min_row=3, max_row=10), start=3):
    pad_id = row[0].value
    if pad_id:
        # 提取SOC数字
        parts = str(pad_id).split('.')
        soc_number = parts[-1] if len(parts) > 1 else str(pad_id)
        
        pads_data.append({
            'pad_id': pad_id,
            'soc_number': soc_number,
            'pad_name': row[1].value if len(row) > 1 else "",
            'x_coord': row[2].value if len(row) > 2 else 0,
            'y_coord': row[3].value if len(row) > 3 else 0,
            'x_open': row[4].value if len(row) > 4 else 0,
            'y_open': row[5].value if len(row) > 5 else 0
        })

# 输出到JSON文件用于检查
with open('pad_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(pads_data, f, indent=2, ensure_ascii=False)

print(f"Analyzed {len(pads_data)} pads")
print("Data saved to pad_analysis.json")
for pad in pads_data[:5]:
    print(f"Pad {pad['pad_id']} -> SOC number: {pad['soc_number']}")

# 检查坐标和尺寸
print("\nCoordinate and size analysis:")
for pad in pads_data[:5]:
    print(f"{pad['pad_id']}: center ({pad['x_coord']}, {pad['y_coord']}), size ({pad['x_open']}x{pad['y_open']})")
