"""
测试基于波动率的随机游走预测
选项B实现
"""
import numpy as np
from datetime import datetime, timedelta

def simulate_price_path(current_price, expected_change, daily_volatility, days=30, random_seed=None):
    """
    模拟价格随机游走路径
    
    Args:
        current_price: 当前价格
        expected_change: 预期总变化率（如0.055表示5.5%）
        daily_volatility: 日波动率
        days: 预测天数
        random_seed: 随机种子（None表示随机）
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    predictions = []
    current_pred = current_price
    daily_drift = expected_change / days
    
    for i in range(1, days + 1):
        # 随机游走: r = drift + volatility * Z
        random_shock = np.random.randn() * daily_volatility
        daily_return = daily_drift + random_shock
        current_pred = current_pred * (1 + daily_return)
        predictions.append(current_pred)
    
    return predictions


print("=" * 70)
print("📊 测试选项B: 基于波动率的随机游走预测")
print("=" * 70)

# 参数设置
current_price = 1150.0
expected_change = 0.055  # 5.5%预期上涨
daily_volatility = 0.15 / np.sqrt(252)  # 约0.0095，即0.95%日波动

print(f"\n参数:")
print(f"  当前价格: {current_price:.2f} 元/克")
print(f"  30天预期变化: {expected_change:.2%}")
print(f"  日波动率: {daily_volatility:.4f} ({daily_volatility*100:.2f}%)")
print(f"  年化波动率: {daily_volatility*np.sqrt(252):.1%}")

# 测试1: 不设置种子（每次不同）
print(f"\n{'='*70}")
print("测试1: 不设置随机种子（模拟5次独立预测）")
print("=" * 70)
print("每次刷新页面都会看到不同的预测路径")
print()

results = []
for run in range(5):
    path = simulate_price_path(current_price, expected_change, daily_volatility, random_seed=None)
    results.append(path[-1])
    print(f"  模拟{run+1}: 第30天 = {path[-1]:.2f} (区间: {min(path):.2f} ~ {max(path):.2f})")

print(f"\n  统计: 平均值={np.mean(results):.2f}, 标准差={np.std(results):.2f}")

# 测试2: 设置相同种子（结果可重现）
print(f"\n{'='*70}")
print("测试2: 设置相同随机种子=42（重现性测试）")
print("=" * 70)
print("使用相同种子可以获得完全相同的预测结果")
print()

for run in range(3):
    path = simulate_price_path(current_price, expected_change, daily_volatility, random_seed=42)
    print(f"  运行{run+1}: 第30天 = {path[-1]:.2f}")

# 测试3: 不同宏观分数的预测
print(f"\n{'='*70}")
print("测试3: 不同宏观评分情景")
print("=" * 70)

scenarios = [
    ("强烈看涨", 0.055),
    ("看涨", 0.02),
    ("中性", 0.0),
    ("看跌", -0.02),
    ("强烈看跌", -0.055)
]

np.random.seed(123)  # 固定种子以便比较
for sentiment, change in scenarios:
    path = simulate_price_path(current_price, change, daily_volatility, random_seed=None)
    direction = "📈" if path[-1] > current_price else "📉" if path[-1] < current_price else "➡️"
    print(f"  {direction} {sentiment:8s} (变化{change:+.1%}): 第30天 = {path[-1]:.2f}")

print(f"\n{'='*70}")
print("✅ 随机游走预测特点:")
print("  1. 每次运行生成不同但统计合理的路径")
print("  2. 整体趋势跟随宏观评分（看涨/看跌）")
    
print(f"  3. 日常波动基于历史波动率（随机但合理）")
print("  4. 可通过random_seed参数重现结果")
print("=" * 70)
