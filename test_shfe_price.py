#!/usr/bin/env python3
"""
测试上海期货交易所黄金数据获取
"""
import sys

def test_shfe_gold():
    """测试上期所黄金数据"""
    print("=" * 60)
    print("🧪 测试上海期货交易所黄金数据获取")
    print("=" * 60)
    
    try:
        import akshare as ak
        print("✅ akshare 已安装")
    except ImportError:
        print("❌ akshare 未安装，请先运行: pip install akshare")
        sys.exit(1)
    
    # 测试获取不同合约数据
    contracts = ['AU2506', 'AU2504', 'AU2412', 'AU2604']
    
    print("\n📊 测试获取各合约数据:")
    for contract in contracts:
        try:
            df = ak.futures_zh_daily_sina(symbol=contract)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                print(f"\n✅ {contract}:")
                print(f"   日期: {latest['date']}")
                print(f"   收盘: {latest['close']} 元/克")
                print(f"   开盘: {latest['open']} 元/克")
                print(f"   最高: {latest['high']} 元/克")
                print(f"   最低: {latest['low']} 元/克")
                print(f"   成交量: {latest['volume']}")
            else:
                print(f"⚠️  {contract}: 无数据")
        except Exception as e:
            print(f"❌ {contract}: {e}")
    
    # 测试实时数据
    print("\n📈 测试实时数据获取:")
    try:
        for contract in ['AU2506', 'AU2504']:
            try:
                df = ak.futures_zh_realtime(symbol=contract)
                if df is not None and not df.empty:
                    print(f"\n✅ {contract} 实时数据:")
                    print(f"   最新价: {df['最新价'].iloc[0]} 元/克")
                    print(f"   涨跌幅: {df['涨跌幅'].iloc[0]}%")
                    break
            except:
                continue
    except Exception as e:
        print(f"⚠️  实时数据获取失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == '__main__':
    test_shfe_gold()
