#!/usr/bin/env python3
"""测试CPI数据获取"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

print("=" * 70)
print("🔍 测试 CPI 数据获取")
print("=" * 70)

from gold_app import MacroFactorCollector
collector = MacroFactorCollector()

print("\n1️⃣ 测试 get_inflation_cpi...")
try:
    cpi = collector.get_inflation_cpi()
    print(f"   ✅ 成功!")
    print(f"   值: {cpi['value']}")
    print(f"   来源: {cpi['data_source']}")
    print(f"   可信度: {cpi['reliability']}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
