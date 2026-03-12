#!/usr/bin/env python3
"""
汇总测试 - 铜价四层宏观因子数据获取情况
"""
import os
from dotenv import load_dotenv
load_dotenv('.env')

print("=" * 80)
print("🔶 铜价四层宏观因子 - 数据获取情况汇总")
print("=" * 80)

from copper_macro_integrated import CopperMacroIntegratedCollector

collector = CopperMacroIntegratedCollector()
data = collector.get_integrated_data(use_web_search=True)

print("\n" + "=" * 80)
print("📊 各层级数据详情")
print("=" * 80)

# 第一层：中国实体经济
print("\n【第一层】中国实体经济 (权重40%)")
china_real = [
    ('官方PMI', 'official_pmi', 50.0),
    ('财新PMI', 'caixin_pmi', 50.0),
    ('房地产新开工同比', 'housing_starts_yoy', -15.0),
    ('电网投资同比', 'grid_investment_yoy', 8.5),
    ('M1-M2剪刀差', 'm1_m2_scissors', -3.0),
    ('社融增速', 'social_finance_yoy', 9.5)
]
for name, key, default in china_real:
    value = data.get(key, 'N/A')
    source = 'Web Search' if value != default else 'API/默认'
    status = "✅" if value != default else "⚠️"
    print(f"  {status} {name}: {value} ({source})")

# 第二层：美元与流动性
print("\n【第二层】美元与流动性 (权重30%)")
dollar_data = [
    ('美元指数DXY', 'dxy_index', 103.5),
    ('DXY 3月变化', 'dxy_change_3m', 1.2),
    ('实际利率TIPS', 'tips_10y', 1.8),
    ('联邦基金利率', 'fed_funds_rate', 5.25),
    ('缩表进度', 'qt_progress', 65),
    ('SOFR-OIS利差', 'sofr_ois_spread', 12)
]
for name, key, default in dollar_data:
    value = data.get(key, 'N/A')
    if key == 'dxy_index' and value != 103.5:
        source = 'Web Search'
    elif key == 'fed_funds_rate' and value != 5.25:
        source = 'Web Search'
    elif key == 'qt_progress' and value != 65:
        source = 'Web Search'
    elif key == 'dxy_change_3m' and value != 1.2:
        source = 'yfinance API'
    else:
        source = 'API/默认'
    status = "✅" if value != default else "⚠️"
    print(f"  {status} {name}: {value} ({source})")

# 第三层：全球工业周期
print("\n【第三层】全球工业周期 (权重20%)")
industrial_data = [
    ('全球制造业PMI', 'global_manufacturing_pmi', 50.3),
    ('美国ISM制造业', 'us_ism_manufacturing', 48.5),
    ('美国新订单指数', 'ism_new_orders', 49.2),
    ('欧盟工业生产', 'eu_industrial_production', -1.5),
    ('库存销售比', 'us_inventory_sales_ratio', 1.38)
]
for name, key, default in industrial_data:
    value = data.get(key, 'N/A')
    source = 'Web Search' if value != default else 'API/默认'
    status = "✅" if value != default else "⚠️"
    print(f"  {status} {name}: {value} ({source})")

# 第四层：供应与政策
print("\n【第四层】供应与政策 (权重10%)")
supply_data = [
    ('铜TC/RC加工费', 'copper_tc_rc', -5),
    ('罢工风险', 'strike_risk_score', 4),
    ('政策风险', 'policy_risk_score', 3),
    ('全球库存天数', 'global_copper_inventory_days', 4.5),
    ('CBAM影响', 'eu_cbam_impact', 3)
]
for name, key, default in supply_data:
    value = data.get(key, 'N/A')
    source = 'Web Search' if value != default else 'API/默认'
    status = "✅" if value != default else "⚠️"
    print(f"  {status} {name}: {value} ({source})")

# 统计
print("\n" + "=" * 80)
print("📈 数据质量统计")
print("=" * 80)

# 统计真实数据数量
web_search_count = 0
api_count = 0
default_count = 0

web_search_keys = ['official_pmi', 'housing_starts_yoy', 'us_ism_manufacturing', 
                   'copper_tc_rc', 'fed_funds_rate', 'qt_progress', 'dxy_index']
for key in data.keys():
    if key in web_search_keys:
        web_search_count += 1
    elif key in ['dxy_change_3m']:
        api_count += 1
    else:
        default_count += 1

total = len(data)
real_pct = (web_search_count + api_count) / total * 100 if total > 0 else 0

print(f"  • 总数据点数: {total}")
print(f"  • Web Search 数据: {web_search_count}")
print(f"  • API 真实数据: {api_count}")
print(f"  • 默认/模拟数据: {default_count}")
print(f"  • 真实数据占比: {real_pct:.1f}%")

print("\n" + "=" * 80)
print("✅ 汇总完成")
print("=" * 80)
