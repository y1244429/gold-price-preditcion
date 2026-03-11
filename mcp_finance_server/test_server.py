#!/usr/bin/env python3
"""
测试金融数据 MCP 服务器
"""

import asyncio
import json
from server import (
    get_gold_futures_daily,
    get_gold_realtime_price,
    get_dxy_index,
    get_us_bond_yield,
    get_vix_index,
    calculate_technical_indicators
)


async def test_all_tools():
    """测试所有工具"""
    print("=" * 60)
    print("🧪 测试金融数据 MCP 服务器")
    print("=" * 60)
    
    # 测试1: 黄金期货日线数据
    print("\n📊 测试1: 获取黄金期货日线数据 (AU2604)...")
    try:
        result = await get_gold_futures_daily({"symbol": "AU2604", "period": "1mo"})
        # TextContent 对象有 text 属性
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功! 最新价格: {data.get('latest_price')} 元/克")
        print(f"   数据条数: {data.get('record_count')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试2: 黄金实时价格
    print("\n💰 测试2: 获取黄金实时价格...")
    try:
        result = await get_gold_realtime_price({"symbol": "AU2604"})
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功! 时间戳: {data.get('timestamp')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试3: 美元指数
    print("\n💵 测试3: 获取美元指数...")
    try:
        result = await get_dxy_index({"period": "1mo"})
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功! 当前值: {data.get('current_value')}")
        print(f"   趋势: {data.get('trend')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试4: 美债收益率
    print("\n📈 测试4: 获取美债收益率...")
    try:
        result = await get_us_bond_yield({"maturity": "10y"})
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功! 10年期收益率: {data.get('current_yield')}%")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试5: VIX指数
    print("\n⚡ 测试5: 获取VIX波动率指数...")
    try:
        result = await get_vix_index({"period": "1mo"})
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功! VIX: {data.get('current_value')} ({data.get('interpretation')})")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试6: 技术指标计算
    print("\n🔧 测试6: 计算技术指标...")
    try:
        # 模拟价格数据
        test_prices = [450, 452, 448, 455, 460, 458, 462, 465, 460, 455, 
                       458, 462, 465, 470, 468, 472, 475, 470, 468, 472]
        result = await calculate_technical_indicators({"prices": test_prices})
        content = result[0]
        data = json.loads(content.text if hasattr(content, 'text') else str(content))
        print(f"✅ 成功!")
        print(f"   RSI(14): {data.get('rsi_14')} ({data.get('rsi_signal')})")
        print(f"   MACD: {data.get('macd')} ({data.get('macd_signal')})")
        print(f"   布林带位置: {data.get('bollinger_position')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("✨ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_tools())
