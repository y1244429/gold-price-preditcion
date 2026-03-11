#!/usr/bin/env python3
"""
验证上海期货交易所黄金价格获取
"""
import sys

def get_shfe_gold_price():
    """获取上海期货交易所黄金当前价格"""
    print("=" * 60)
    print("🔍 验证上海期货交易所黄金价格获取")
    print("=" * 60)
    
    try:
        import akshare as ak
        print("✅ akshare 已加载")
    except ImportError:
        print("❌ akshare 未安装")
        print("请先运行: pip install akshare")
        return None, None
    
    # 尝试获取各合约数据
    contracts = ['AU2506', 'AU2504', 'AU2412', 'AU2604', 'AU0']
    
    print("\n📊 尝试获取各合约数据:\n")
    
    for contract in contracts:
        try:
            df = ak.futures_zh_daily_sina(symbol=contract)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                price = float(latest['close'])
                date = latest['date']
                
                print(f"✅ {contract} 合约:")
                print(f"   日期: {date}")
                print(f"   收盘价: {price:.2f} 元/克")
                print(f"   开盘价: {latest['open']:.2f} 元/克")
                print(f"   最高价: {latest['high']:.2f} 元/克")
                print(f"   最低价: {latest['low']:.2f} 元/克")
                print(f"   成交量: {latest['volume']}")
                print()
                
                return price, contract
            else:
                print(f"⚠️  {contract}: 返回空数据")
        except Exception as e:
            print(f"❌ {contract}: {str(e)[:50]}")
    
    return None, None

def main():
    price, contract = get_shfe_gold_price()
    
    print("=" * 60)
    if price:
        print(f"✅ 成功获取上海期货交易所黄金价格")
        print(f"   合约: {contract}")
        print(f"   价格: {price:.2f} 元/克 (RMB)")
        print(f"   注意: 这是人民币/克的价格，不是美元/盎司")
    else:
        print("❌ 无法获取上海期货交易所数据")
        print("   可能原因:")
        print("   1. akshare 版本过旧: pip install --upgrade akshare")
        print("   2. 网络连接问题")
        print("   3. 合约代码变更")
    print("=" * 60)

if __name__ == '__main__':
    main()
