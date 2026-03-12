#!/usr/bin/env python3
"""
测试数据来源是否正确包含在宏观因子结果中
"""
import os
from dotenv import load_dotenv
load_dotenv('.env')

from copper_macro_factors import CopperMacroAdjustmentSystem, get_default_macro_data

print("=" * 70)
print("🔍 测试数据来源标记")
print("=" * 70)

# 获取宏观数据
macro_data = get_default_macro_data()

# 计算宏观因子
system = CopperMacroAdjustmentSystem()
result = system.calculate(macro_data)

print("\n📊 四层宏观因子数据来源:\n")

for layer_key, layer in result['layers'].items():
    print(f"\n【{layer['name']}】")
    print("-" * 50)
    
    for factor in layer['factors']:
        source = factor.get('data_source', '模拟数据')
        status = "✅" if source in ['Web Search', 'yfinance API'] else "⚠️"
        print(f"  {status} {factor['name']}: {source}")

print("\n" + "=" * 70)
print("✅ 测试完成")
print("=" * 70)
