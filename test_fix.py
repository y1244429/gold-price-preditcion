#!/usr/bin/env python3
"""
测试修复后的黄金价格获取
"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

def test_price_fetch():
    """测试价格获取"""
    print("=" * 70)
    print("🧪 测试修复后的黄金价格获取")
    print("=" * 70)
    
    # 测试上海期货交易所数据获取
    print("\n1. 测试上海期货交易所数据获取...")
    try:
        from gold_app import get_shfe_gold_data
        df = get_shfe_gold_data()
        if df is not None and not df.empty:
            latest_price = df['Close'].iloc[-1]
            source = df.attrs.get('data_source', '未知')
            print(f"   ✅ 成功获取: {latest_price:.2f} 元/克")
            print(f"   ✅ 数据来源: {source}")
        else:
            print("   ❌ 获取失败")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试宏观预测中的价格获取
    print("\n2. 测试宏观预测价格获取逻辑...")
    try:
        from gold_app import MacroFactorCollector
        collector = MacroFactorCollector()
        
        # 模拟因子数据
        mock_factors = {
            '美元指数 (DXY)': {'value': 103.5, 'change_1m': 0.5, 'trend': 'up', 'weight': 0.20, 'impact': 'negative'},
            '实际利率 (TIPS)': {'value': 1.5, 'change_1m': 0.1, 'trend': 'up', 'weight': 0.18, 'impact': 'negative'},
            '通胀预期 (CPI)': {'value': 2.5, 'change_1m': 0.1, 'trend': 'up', 'weight': 0.15, 'impact': 'positive'},
        }
        mock_scores = {}
        mock_total = 5.5
        
        prediction = collector.predict_price(mock_factors, mock_scores, mock_total)
        
        print(f"   ✅ 当前价格: {prediction['current_price']:.2f}")
        print(f"   ✅ 价格来源: {prediction.get('current_price_source', '未知')}")
        print(f"   ✅ 合约代码: {prediction.get('current_price_contract', 'N/A')}")
        
        # 验证价格单位
        if prediction['current_price'] > 1000:
            print(f"   ⚠️  价格超过1000，可能是美元/盎司单位")
        elif prediction['current_price'] > 500 and prediction['current_price'] < 1000:
            print(f"   ✅ 价格在500-1000之间，符合人民币/克单位")
        else:
            print(f"   ⚠️  价格异常，请检查")
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("\n💡 预期结果:")
    print("   - 当前价格应该是 791.00 元/克左右")
    print("   - 数据来源应该是 '上海期货交易所'")
    print("   - 合约代码应该是 'AU2506'")
    print("=" * 70)

if __name__ == '__main__':
    test_price_fetch()
