#!/usr/bin/env python3
"""快速测试宏观数据获取"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

print("=" * 70)
print("📊 快速测试改进后的宏观数据获取")
print("=" * 70)

try:
    from gold_app import MacroFactorCollector
    collector = MacroFactorCollector()
    
    print("\n1️⃣ 测试美元指数获取...")
    dxy = collector.get_dxy()
    print(f"   值: {dxy['value']}, 来源: {dxy['data_source']}, 可信度: {dxy['reliability']}")
    
    print("\n2️⃣ 测试通胀预期获取...")
    cpi = collector.get_inflation_cpi()
    print(f"   值: {cpi['value']}, 来源: {cpi['data_source']}, 可信度: {cpi['reliability']}")
    
    print("\n3️⃣ 测试金银比获取...")
    ratios = collector.get_gold_ratios()
    print(f"   值: {ratios['value']}, 来源: {ratios['data_source']}, 可信度: {ratios['reliability']}")
    
    print("\n4️⃣ 测试ETF持仓获取...")
    etf = collector.get_etf_holdings()
    print(f"   值: {etf['value']}, 来源: {etf['data_source']}, 可信度: {etf['reliability']}")
    
    print("\n✅ 核心数据测试完成!")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
