"""
测试增强版GPR/EPU数据获取
"""
import sys
import os

print("=" * 70)
print("📊 测试增强版宏观因子数据获取")
print("=" * 70)

# 测试1: 直接获取GPR数据
print("\n1️⃣  测试GPR数据获取...")
print("-" * 70)
try:
    from enhanced_gpr_epu import get_gpr_index
    gpr = get_gpr_index()
    
    if gpr.get('value') is not None:
        print(f"✅ GPR数据获取成功!")
        print(f"   当前值: {gpr['value']}")
        print(f"   数据源: {gpr['data_source']}")
        print(f"   可信度: {gpr['reliability']}")
        print(f"   趋势: {gpr['trend']}")
    else:
        print(f"❌ GPR数据获取失败: {gpr.get('error')}")
except Exception as e:
    print(f"❌ GPR测试出错: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 直接获取EPU数据
print("\n2️⃣  测试EPU数据获取...")
print("-" * 70)
try:
    from enhanced_gpr_epu import get_epu_index
    
    # 测试中国EPU
    epu_cn = get_epu_index('China')
    if epu_cn.get('value') is not None:
        print(f"✅ EPU-China数据获取成功!")
        print(f"   当前值: {epu_cn['value']}")
        print(f"   数据源: {epu_cn['data_source']}")
    else:
        print(f"⚠️  EPU-China获取失败: {epu_cn.get('error')}")
    
    # 测试美国EPU
    epu_us = get_epu_index('US')
    if epu_us.get('value') is not None:
        print(f"✅ EPU-US数据获取成功!")
        print(f"   当前值: {epu_us['value']}")
        print(f"   数据源: {epu_us['data_source']}")
    else:
        print(f"⚠️  EPU-US获取失败: {epu_us.get('error')}")
        
except Exception as e:
    print(f"❌ EPU测试出错: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 集成到MacroFactorCollector
print("\n3️⃣  测试集成到MacroFactorCollector...")
print("-" * 70)
try:
    from gold_app import MacroFactorCollector
    
    collector = MacroFactorCollector()
    
    # 测试GPR
    print("   测试 get_gpr()...")
    gpr_data = collector.get_gpr()
    print(f"   GPR: {gpr_data.get('value')} (来源: {gpr_data.get('data_source', 'N/A')[:40]}...)")
    
    # 测试EPU
    print("   测试 get_epu()...")
    epu_data = collector.get_epu()
    print(f"   EPU: {epu_data.get('value')} (来源: {epu_data.get('data_source', 'N/A')[:40]}...)")
    
except Exception as e:
    print(f"❌ 集成测试出错: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ 测试完成!")
print("=" * 70)
print("\n如果以上测试成功，现在可以启动主应用:")
print("   python gold_app.py")
print("\n然后访问: http://127.0.0.1:8080/api/macro-factors")
