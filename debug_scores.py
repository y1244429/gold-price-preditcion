"""
调试宏观因子评分计算
"""
import sys
sys.path.insert(0, '.')

from gold_app import MacroFactorCollector
import numpy as np

print("=" * 70)
print("📊 宏观因子评分调试")
print("=" * 70)

collector = MacroFactorCollector()

# 获取所有因子
print("\n1️⃣  获取原始因子数据...")
factors = collector.get_all_factors()

print("\n2️⃣  各因子原始值:")
print("-" * 70)
for name, data in factors.items():
    print(f"{name:20s}: 值={data['value']}, 趋势={data.get('trend', 'N/A')}, 变化={data.get('change_1m', 0)}")

# 计算得分
print("\n3️⃣  评分计算详情:")
print("-" * 70)
print(f"{'因子名':<20s} {'基础分':>8s} {'趋势':>6s} {'变化':>6s} {'原始':>6s} {'调整':>6s} {'加权':>8s}")
print("-" * 70)

total_score = 0
scores = {}

for name, data in factors.items():
    # 基础分值 (0-10)
    if isinstance(data['value'], dict):
        base_score = 5.0
    else:
        base_score = collector._normalize_value(name, data['value'])
    
    # 趋势调整
    trend_bonus = 1.5 if data['trend'] == 'up' else -1.5
    
    # 变化率调整
    change_bonus = np.clip(data['change_1m'] * 0.5, -2, 2)
    
    # 最终得分
    raw_score = base_score + trend_bonus + change_bonus
    final_score = np.clip(raw_score, 0, 10)
    
    # 根据影响方向调整
    if data['impact'] == 'negative':
        adjusted_score = 10 - final_score
    else:
        adjusted_score = final_score
    
    weighted_score = adjusted_score * data['weight']
    total_score += weighted_score
    
    print(f"{name:<18s}: {base_score:>8.2f} {trend_bonus:>+6.1f} {change_bonus:>+6.1f} {final_score:>6.2f} {adjusted_score:>6.2f} {weighted_score:>8.3f}")
    
    scores[name] = {
        'base_score': base_score,
        'trend_bonus': trend_bonus,
        'change_bonus': change_bonus,
        'final_score': final_score,
        'adjusted_score': adjusted_score,
        'weighted_score': weighted_score,
        'weight': data['weight'],
        'impact': data['impact']
    }

print("-" * 70)
print(f"{'总分':<18s}: {'':>8s} {'':>6s} {'':>6s} {'':>6s} {'':>6s} {total_score:>8.3f}")
print("=" * 70)

print(f"\n📈 总分: {total_score:.3f}")
print(f"\n解读:")
if total_score > 6.5:
    print("   强烈看涨 (expected_change = +5.5%)")
elif total_score > 5.5:
    print("   看涨 (expected_change = +2%)")
elif total_score > 4.5:
    print("   中性 (expected_change = 0%) ← 当前情况")
elif total_score > 3.5:
    print("   看跌 (expected_change = -2%)")
else:
    print("   强烈看跌 (expected_change = -5.5%)")

print("\n" + "=" * 70)
print("💡 分析:")
print("=" * 70)
print("总分 = Σ(调整后得分 × 权重)")
print("\n权重分布:")
for name, s in scores.items():
    bar = "█" * int(s['weight'] * 50)
    print(f"   {name:<20s}: {s['weight']:.2f} {bar}")
