"""
铜价宏观调整因子系统 - 测试与分析脚本

提供多种宏观情景测试和对比分析
"""
from copper_macro_factors import calculate_copper_adjustment, CopperMacroAdjustmentSystem
from datetime import datetime
import json


def create_scenario(name: str, data: dict) -> dict:
    """创建测试场景"""
    base_data = {
        # 中国房地产数据
        'housing_starts_yoy': -15,
        'housing_completed_yoy': -10,
        'construction_yoy': -8,
        # 基建投资
        'grid_investment_yoy': 8,
        'transport_investment_yoy': 4,
        # PMI
        'official_pmi': 50.0,
        'caixin_pmi': 50.0,
        # 信贷
        'social_finance_yoy': 9,
        'm1_m2_scissors': -3,
        # 美元流动性
        'dxy_index': 103,
        'dxy_change_3m': 0,
        'tips_10y': 1.8,
        'fed_funds_rate': 5.25,
        'qt_progress': 60,
        'sofr_ois_spread': 15,
        'fra_ois_spread': 20,
        # 全球工业
        'global_manufacturing_pmi': 50.0,
        'us_ism_manufacturing': 49.0,
        'ism_new_orders': 49.0,
        'eu_industrial_production': -1,
        'us_inventory_sales_ratio': 1.40,
        # 供应与政策
        'copper_tc_rc': 20,
        'chile_copper_output': 0,
        'peru_copper_output': 0,
        'strike_risk_score': 3,
        'policy_risk_score': 3,
        'global_copper_inventory_days': 5,
        'eu_cbam_impact': 3,
        'china_energy_control': 4
    }
    base_data.update(data)
    return {'name': name, 'data': base_data}


def run_scenario(scenario: dict) -> dict:
    """运行单个场景测试"""
    print("\n" + "=" * 70)
    print(f"📊 场景: {scenario['name']}")
    print("=" * 70)
    
    result = calculate_copper_adjustment(scenario['data'])
    
    system = CopperMacroAdjustmentSystem()
    print(system.get_summary(result))
    
    return {
        'scenario': scenario['name'],
        'composite_score': result['composite_score'],
        'signal': result['signal'],
        'adjustment_pct': result['adjustment']['price_adjustment_pct'],
        'confidence': result['overall_confidence'],
        'layers': {
            'china': result['layers']['china_real_economy']['score'],
            'dollar': result['layers']['dollar_liquidity']['score'],
            'industrial': result['layers']['global_industrial']['score'],
            'supply': result['layers']['supply_policy']['score']
        }
    }


def print_comparison(results: list):
    """打印场景对比"""
    print("\n" + "=" * 70)
    print("📈 多场景对比分析")
    print("=" * 70)
    print(f"{'场景':<20} {'综合得分':>10} {'调整幅度':>12} {'信号':>10} {'置信度':>10}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['scenario']:<20} {r['composite_score']:>+10.3f} {r['adjustment_pct']:>+11.1f}% {r['signal']:>10} {r['confidence']:>9.1%}")
    
    print("\n" + "-" * 70)
    print("各层级得分对比:")
    print(f"{'场景':<20} {'中国实体':>10} {'美元流动':>10} {'全球工业':>10} {'供应政策':>10}")
    print("-" * 70)
    for r in results:
        print(f"{r['scenario']:<20} {r['layers']['china']:>+10.3f} {r['layers']['dollar']:>+10.3f} {r['layers']['industrial']:>+10.3f} {r['layers']['supply']:>+10.3f}")


def main():
    """主测试函数"""
    
    # 定义测试场景
    scenarios = [
        create_scenario("基准情景", {}),
        
        create_scenario("乐观情景", {
            'housing_starts_yoy': -5,      # 房地产改善
            'official_pmi': 52.0,           # PMI扩张
            'caixin_pmi': 52.5,
            'dxy_index': 100.0,             # 美元走弱
            'dxy_change_3m': -3.0,
            'tips_10y': 1.0,                # 实际利率下降
            'fed_funds_rate': 4.0,          # 降息
            'global_manufacturing_pmi': 52.0,
            'us_ism_manufacturing': 53.0,
            'copper_tc_rc': -10,            # 供应紧张
            'global_copper_inventory_days': 3
        }),
        
        create_scenario("悲观情景", {
            'housing_starts_yoy': -25,      # 房地产恶化
            'official_pmi': 47.0,           # PMI收缩
            'caixin_pmi': 47.5,
            'dxy_index': 106.0,             # 美元走强
            'dxy_change_3m': 3.0,
            'tips_10y': 2.5,                # 实际利率上升
            'fed_funds_rate': 5.5,          # 加息
            'global_manufacturing_pmi': 48.0,
            'us_ism_manufacturing': 46.0,
            'copper_tc_rc': 50,             # 供应宽松
            'global_copper_inventory_days': 7
        }),
        
        create_scenario("中国复苏", {
            'housing_starts_yoy': -5,       # 房地产改善
            'grid_investment_yoy': 15,      # 基建发力
            'transport_investment_yoy': 10,
            'official_pmi': 52.5,
            'caixin_pmi': 53.0,
            'social_finance_yoy': 12,
            'm1_m2_scissors': 1.0
        }),
        
        create_scenario("美元宽松", {
            'dxy_index': 100.0,
            'dxy_change_3m': -2.5,
            'tips_10y': 1.2,
            'fed_funds_rate': 4.0,
            'qt_progress': 30,
            'sofr_ois_spread': 8,
            'fra_ois_spread': 12
        }),
        
        create_scenario("供应冲击", {
            'copper_tc_rc': -20,            # 极端供应紧张
            'chile_copper_output': -10,
            'peru_copper_output': -15,
            'strike_risk_score': 7,
            'global_copper_inventory_days': 2.5
        })
    ]
    
    # 运行所有场景
    results = []
    for scenario in scenarios:
        result = run_scenario(scenario)
        results.append(result)
    
    # 对比分析
    print_comparison(results)
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'scenarios': results
    }
    
    output_file = f"/Users/ydy/CodeBuddy/20260310193311/output/copper_macro_scenarios_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print(f"💾 结果已保存: {output_file}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()
