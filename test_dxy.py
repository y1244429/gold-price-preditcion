#!/usr/bin/env python3
"""测试美元指数数据获取"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

print("=" * 70)
print("🔍 测试美元指数数据获取")
print("=" * 70)

from gold_app import MacroFactorCollector
collector = MacroFactorCollector()

print("\n1️⃣ 测试 get_dxy...")
try:
    dxy = collector.get_dxy()
    print(f"   ✅ 成功!")
    print(f"   值: {dxy['value']}")
    print(f"   来源: {dxy['data_source']}")
    print(f"   可信度: {dxy['reliability']}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
