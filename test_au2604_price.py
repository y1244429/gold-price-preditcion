#!/usr/bin/env python3
"""测试 AU2604 实时价格获取"""
import akshare as ak
from datetime import datetime

print("=" * 60)
print(f"AU2604 实时价格测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 方法1: 获取日线数据
try:
    print("\n1. 获取 AU2604 日线数据...")
    df = ak.futures_zh_daily_sina(symbol='AU2604')
    if df is not None and not df.empty:
        latest_close = df['close'].iloc[-1]
        latest_date = df['date'].iloc[-1]
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else latest_close
        change = latest_close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
        print(f"   ✓ 最新收盘价: {latest_close} 元/克")
        print(f"   ✓ 涨跌: {change:+.2f} ({change_pct:+.2f}%)")
        print(f"   ✓ 数据日期: {latest_date}")
        print(f"   ✓ 数据条数: {len(df)}")
    else:
        print("   ✗ 数据为空")
except Exception as e:
    print(f"   ✗ 获取失败: {e}")

# 方法2: 尝试使用 futures_zh_spot 获取上海期货交易所实时行情
try:
    print("\n2. 获取上海期货交易所黄金期货实时行情...")
    df_spot = ak.futures_zh_spot(symbol='AU2604')
    if df_spot is not None and not df.empty:
        print(f"   列名: {df_spot.columns.tolist()}")
        print(f"   数据:\n{df_spot}")
    else:
        print("   ✗ 数据为空")
except Exception as e:
    print(f"   ✗ 获取失败: {e}")

# 方法3: 尝试获取主力合约连续行情
try:
    print("\n3. 获取黄金主力连续合约...")
    df_main = ak.futures_zh_daily_sina(symbol='AU0')  # 主力连续
    if df_main is not None and not df_main.empty:
        latest_main = df_main['close'].iloc[-1]
        print(f"   ✓ AU0 主力连续最新价: {latest_main} 元/克")
    else:
        print("   ✗ 数据为空")
except Exception as e:
    print(f"   ✗ 获取失败: {e}")

print("\n" + "=" * 60)
print("说明:")
print("- 日线数据是昨日收盘价（收盘后更新）")
print("- 如果您看到的价格是1154，可能是:")
print("  1. 实时行情价格（盘中交易时）")
print("  2. 不同的数据源")
print("  3. 延迟更新的数据")
print("=" * 60)
