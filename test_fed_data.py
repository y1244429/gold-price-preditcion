#!/usr/bin/env python3
"""
测试美联储政策数据 Web Search 获取
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('.env')

print("=" * 70)
print("🧪 美联储政策数据 - Web Search 测试")
print("=" * 70)

# 导入搜索类
from copper_macro_web_search import CopperMacroWebSearch

searcher = CopperMacroWebSearch()

# 测试获取美联储政策数据
print("\n📊 测试获取美联储政策数据...\n")
fed_data = searcher.get_fed_policy_data()

print("\n" + "=" * 70)
print("📋 获取到的美联储数据:")
print("=" * 70)

if fed_data:
    for key, value in fed_data.items():
        print(f"  • {key}: {value}")
else:
    print("  ⚠️ 未获取到数据")

# 与默认值对比
print("\n" + "=" * 70)
print("📊 与默认值对比:")
print("=" * 70)
defaults = {
    'fed_funds_rate': 5.25,
    'dxy_index': 103.5,
    'qt_progress': 65
}

for key in ['fed_funds_rate', 'dxy_index']:
    web_value = fed_data.get(key, '未获取')
    default_value = defaults.get(key, 'N/A')
    status = "✅ 已更新" if key in fed_data else "⚠️ 使用默认"
    print(f"  {status} {key}: {web_value} (默认: {default_value})")

print("\n" + "=" * 70)
print("✅ 测试完成")
print("=" * 70)
