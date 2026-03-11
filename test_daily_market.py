#!/usr/bin/env python3
"""
每日市场数据推送测试
"""

import akshare as ak
import yfinance as yf
from datetime import datetime

def get_daily_market_data():
    """获取每日市场数据"""
    print('📊 每日市场数据推送测试')
    print('=' * 50)
    
    # 1. 获取上期所黄金数据
    try:
        df = ak.futures_zh_daily_sina(symbol='AU2604')
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change = (latest['close'] - prev['close']) / prev['close'] * 100
            print(f'\n📈 上期所 AU2604 黄金期货')
            print(f'   日期: {latest["date"]}')
            print(f'   收盘价: {latest["close"]:.2f} 元/克')
            print(f'   涨跌: {change:+.2f}%')
            print(f'   开盘价: {latest["open"]:.2f} 元/克')
            print(f'   最高价: {latest["high"]:.2f} 元/克')
            print(f'   最低价: {latest["low"]:.2f} 元/克')
            print(f'   成交量: {int(latest["volume"])}')
    except Exception as e:
        print(f'❌ 黄金数据获取失败: {e}')
    
    # 2. 获取美元指数
    try:
        dxy = yf.Ticker('DX-Y.NYB').history(period='5d')
        if not dxy.empty:
            current = dxy['Close'].iloc[-1]
            prev = dxy['Close'].iloc[-2]
            change = (current - prev) / prev * 100
            print(f'\n💵 美元指数 (DXY)')
            print(f'   当前: {current:.2f}')
            print(f'   涨跌: {change:+.2f}%')
            print(f'   对黄金影响: {"利空" if change > 0 else "利好"}')
    except Exception as e:
        print(f'❌ 美元指数获取失败: {e}')
    
    # 3. 获取VIX
    try:
        vix = yf.Ticker('^VIX').history(period='5d')
        if not vix.empty:
            current = vix['Close'].iloc[-1]
            print(f'\n⚡ VIX波动率指数')
            print(f'   当前: {current:.2f}')
            print(f'   情绪: {"恐慌" if current > 30 else "正常" if current > 20 else "低迷"}')
            print(f'   对黄金影响: {"利好(避险)" if current > 25 else "中性"}')
    except Exception as e:
        print(f'❌ VIX获取失败: {e}')
    
    # 4. 获取美债收益率
    try:
        tnx = yf.Ticker('^TNX').history(period='5d')
        if not tnx.empty:
            current = tnx['Close'].iloc[-1]
            prev = tnx['Close'].iloc[-2]
            change = current - prev
            print(f'\n📊 美债10年期收益率')
            print(f'   当前: {current:.3f}%')
            print(f'   涨跌: {change:+.3f}%')
            print(f'   对黄金影响: {"利空" if change > 0 else "利好"}')
    except Exception as e:
        print(f'❌ 美债收益率获取失败: {e}')
    
    # 5. 获取铜价（铜金比）
    try:
        copper = yf.Ticker('HG=F').history(period='5d')
        if not copper.empty:
            current = copper['Close'].iloc[-1]
            print(f'\n🔶 铜期货价格')
            print(f'   当前: {current:.4f} USD/lb')
    except Exception as e:
        print(f'❌ 铜价获取失败: {e}')
    
    print('\n' + '=' * 50)
    print(f'✅ 数据更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('\n💡 总结:')
    print('   以上数据可用于黄金价格预测模型的输入特征')

if __name__ == '__main__':
    get_daily_market_data()
