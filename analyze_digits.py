from data_handlers import ExcelHandler

# 检查pad编号的位数分布
handler = ExcelHandler()
handler.read_excel("封装连线示意.xlsx")
pads = handler.get_pads()

digit_counts = {}
max_number_length = 0
max_number = ""
three_digit_pads = []

for pad in pads:
    parts = pad.pad_id.split('.')
    pad_number = parts[-1] if len(parts) > 1 else str(pad.pad_id)
    
    digit_count = len(pad_number)
    digit_counts[digit_count] = digit_counts.get(digit_count, 0) + 1
    
    if digit_count > max_number_length:
        max_number_length = digit_count
        max_number = pad_number
    
    if digit_count >= 3:
        three_digit_pads.append(pad.pad_id)

print("Pad Number Digit Distribution:")
print("="*40)
for digits in sorted(digit_counts.keys()):
    print(f"{digits}-digit numbers: {digit_counts[digits]} pads")

print(f"\nMaximum number: '{max_number}' ({max_number_length} digits)")

if three_digit_pads:
    print(f"\n3-digit (or more) pad examples:")
    for pad_id in three_digit_pads[:10]:
        print(f"  {pad_id}")
else:
    print("\nNo 3-digit pad numbers found")

# 分析pad尺寸
min_x = min(p.x_open for p in pads)
max_x = max(p.x_open for p in pads)
min_y = min(p.y_open for p in pads)  
max_y = max(p.y_open for p in pads)

print(f"\nPad Size Distribution:")
print(f"  X dimension: {min_x:.2f} to {max_x:.2f}")
print(f"  Y dimension: {min_y:.2f} to {max_y:.2f}")

# 计算最小的pad尺寸
smallest_pads = []
smallest_dim = float('inf')
for pad in pads:
    pad_dim = min(pad.x_open, pad.y_open)
    if pad_dim < smallest_dim:
        smallest_dim = pad_dim

print(f"\nSmallest pad dimension: {smallest_dim:.2f}")

# 找出最小尺寸的pads
for pad in pads:
    if min(pad.x_open, pad.y_open) == smallest_dim:
        smallest_pads.append(pad._get_pad_id_text() if hasattr(pad, '_get_pad_id_text') else pad.pad_id)

print(f"Pads with smallest size: {smallest_pads[:5]}")

# 计算推荐的字体大小
if smallest_dim > 0:
    print(f"\nRecommended font sizes for smallest pad:")
    print(f"  1-digit: {smallest_dim / 2:.1f}")
    print(f"  2-digit: {smallest_dim / 2.5:.1f}")
    print(f"  3-digit: {smallest_dim / 3.5:.1f}")
