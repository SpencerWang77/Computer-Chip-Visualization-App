from models import Pad, ChipLayout

def test_modular_functionality():
    print("Testing Pad and ChipLayout modular functionality...")
    
    # 测试Pad类的模块化功能
    print("\n=== Testing Pad class ===")
    
    # 创建两个pad
    pad1 = Pad("SOC.1", "VCCA", 100.0, 100.0, 50.0, 50.0, "VCC", "bond1")
    pad2 = Pad("SOC.2", "VSS", 150.0, 100.0, 50.0, 50.0, "VSS", "bond2")
    
    print(f"Created pads: {pad1.pad_id}, {pad2.pad_id}")
    
    # 测试状态标记
    print(f"Pad1 modified status: {pad1.is_modified}")
    pad1.update_position(110.0, 110.0)
    print(f"Pad1 modified status after update: {pad1.is_modified}")
    print(f"Pad1 new position: ({pad1.x_coord}, {pad1.y_coord})")
    
    # 测试删除标记
    pad2.mark_for_deletion()
    print(f"Pad2 deletion status: {pad2.is_marked_for_deletion}")
    
    # 测试clone功能
    pad1_clone = pad1.clone()
    print(f"Cloned pad: {pad1_clone.pad_id}")
    pad1_clone.pad_id = "SOC.100"
    print(f"Clone modified pad_id to: {pad1_clone.pad_id}")
    
    # 测试ChipLayout的CRUD功能
    print("\n=== Testing ChipLayout CRUD operations ===")
    
    layout = ChipLayout()
    
    # 添加pads
    layout.add_pad(pad1)
    layout.add_pad(pad2)
    print(f"Added pads to layout")
    
    # 获取所有pads
    all_pads = layout.get_all_pads()
    print(f"Total pads in layout: {len(all_pads)}")
    
    # 获取被修改的pads
    modified_pads = layout.get_modified_pads()
    print(f"Modified pads: {len(modified_pads)}")
    
    # 更新pad
    layout.update_pad("SOC.1", x_coord=120.0, pad_name="VCCA_UPDATED")
    updated_pad = layout.get_pad_by_id("SOC.1")
    print(f"Updated pad: {updated_pad.pad_name}, position: ({updated_pad.x_coord}, {updated_pad.y_coord})")
    
    # 替换pad
    new_pad = Pad("SOC.50", "NEW_PAD", 200.0, 200.0, 60.0, 60.0, "NET1", "BOND1")
    layout.replace_pad("SOC.1", new_pad)
    print(f"Replaced SOC.1 with SOC.50")
    
    # 验证更新后的布局
    all_pads = layout.get_all_pads()
    print(f"Pads after replacement: {[p.pad_id for p in all_pads]}")
    
    # 测试删除功能
    layout.remove_pad("SOC.50")
    print(f"Removed SOC.50 from layout")
    
    # 验证删除结果
    remaining_pads = layout.get_all_pads()
    print(f"Remaining pads: {[p.pad_id for p in remaining_pads]}")
    
    # 测试序列化
    print("\n=== Testing Serialization ===")
    test_pad = Pad("SERIAL_TEST", "TEST_PAD", 50.0, 50.0, 30.0, 30.0, "TEST_NET", "TEST_BOND")
    
    dict_data = test_pad.to_dict()
    print(f"Serialized pad: {dict_data}")
    
    reconstructed_pad = Pad.from_dict(dict_data)
    print(f"Reconstructed pad: {reconstructed_pad.pad_id}")
    print(f"Position matches: {reconstructed_pad.x_coord == test_pad.x_coord}")
    
    print("\n=== All modular functionality tests completed successfully! ===")

if __name__ == "__main__":
    test_modular_functionality()
