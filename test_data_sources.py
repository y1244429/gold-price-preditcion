#!/usr/bin/env python3
"""测试各个数据源的可用性"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

print("=" * 70)
print("🔍 测试数据源可用性")
print("=" * 70)

# 测试1: akshare 外汇数据
print("\n1️⃣ 测试 akshare 外汇数据 (美元指数)...")
try:
    import akshare as ak
    
    # 测试中国银行外汇牌价
    print("   测试 currency_boc_sina...")
    usd_cny = ak.currency_boc_sina(symbol="美元")
    print(f"   ✅ 成功! 数据行数: {len(usd_cny)}")
    print(f"   列名: {list(usd_cny.columns)}")
    print(f"   最新数据:\n{usd_cny.tail(1)}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试2: akshare CPI数据
print("\n2️⃣ 测试 akshare CPI数据...")
try:
    import akshare as ak
    
    print("   测试 macro_china_cpi...")
    cpi_df = ak.macro_china_cpi()
    print(f"   ✅ 成功! 数据行数: {len(cpi_df)}")
    print(f"   列名: {list(cpi_df.columns)}")
    print(f"   最新数据:\n{cpi_df.tail(1)}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试3: GPR/EPU 数据
print("\n3️⃣ 测试 enhanced_gpr_epu 模块...")
try:
    from enhanced_gpr_epu import EnhancedDataCollector
    collector = EnhancedDataCollector()
    
    print("   测试 GPR 数据获取...")
    gpr_result = collector.get_gpr_data()
    if gpr_result.get('status') == 'success':
        print(f"   ✅ GPR 成功! 值: {gpr_result['value']}")
    else:
        print(f"   ❌ GPR 失败: {gpr_result.get('error')}")
    
    print("   测试 EPU-China 数据获取...")
    epu_cn_result = collector.get_epu_data('China')
    if epu_cn_result.get('status') == 'success':
        print(f"   ✅ EPU-China 成功! 值: {epu_cn_result['value']}")
    else:
        print(f"   ❌ EPU-China 失败: {epu_cn_result.get('error')}")
    
    print("   测试 EPU-US 数据获取...")
    epu_us_result = collector.get_epu_data('US')
    if epu_us_result.get('status') == 'success':
        print(f"   ✅ EPU-US 成功! 值: {epu_us_result['value']}")
    else:
        print(f"   ❌ EPU-US 失败: {epu_us_result.get('error')}")
        
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 检查缓存文件
print("\n4️⃣ 检查缓存文件...")
import os
cache_files = [
    './data_cache/gpr_daily.xls',
    './data_cache/epu_china.xlsx',
    './data_cache/epu_us.xlsx'
]
for cf in cache_files:
    if os.path.exists(cf):
        print(f"   ✅ {cf} 存在")
    else:
        print(f"   ❌ {cf} 不存在")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
