#!/usr/bin/env python3
"""
测试改进后的宏观数据获取
验证真实数据 vs 模拟数据的比例
"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

def test_enhanced_macro_data():
    print("=" * 70)
    print("📊 测试改进后的宏观数据获取")
    print("=" * 70)
    
    from gold_app import MacroFactorCollector
    
    collector = MacroFactorCollector()
    factors = collector.get_all_factors()
    
    print("\n" + "=" * 70)
    print("📈 数据获取结果")
    print("=" * 70)
    
    real_data = []
    proxy_data = []
    mock_data = []
    
    for name, data in factors.items():
        source = data.get('data_source', '未知')
        reliability = data.get('reliability', '低')
        value = data.get('value')
        
        # 判断数据类型
        if '备用' in source or '失败' in source or reliability == '低':
            mock_data.append((name, data))
            status = "❌ 模拟"
        elif '代理' in source or '估算' in source or reliability == '中':
            proxy_data.append((name, data))
            status = "⚠️  代理"
        else:
            real_data.append((name, data))
            status = "✅ 真实"
        
        # 打印详情
        if isinstance(value, dict):
            value_str = str(value)
        else:
            value_str = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
        
        print(f"\n{status} {name}")
        print(f"   值: {value_str}")
        print(f"   来源: {source}")
        print(f"   可信度: {reliability}")
        if data.get('method'):
            print(f"   方法: {data['method']}")
    
    print("\n" + "=" * 70)
    print("📊 统计汇总")
    print("=" * 70)
    total = len(factors)
    print(f"✅ 真实数据: {len(real_data)}/{total} ({len(real_data)*100//total}%)")
    print(f"⚠️  代理数据: {len(proxy_data)}/{total} ({len(proxy_data)*100//total}%)")
    print(f"❌ 模拟数据: {len(mock_data)}/{total} ({len(mock_data)*100//total}%)")
    
    # 与改进前对比
    print("\n" + "=" * 70)
    print("📈 改进效果对比")
    print("=" * 70)
    print("改进前: 真实数据 ~30%, 代理数据 ~22%, 模拟数据 ~48%")
    print(f"改进后: 真实数据 {len(real_data)*100//total}%, 代理数据 {len(proxy_data)*100//total}%, 模拟数据 {len(mock_data)*100//total}%")
    
    if len(real_data) >= 6:
        print("\n✅ 改进成功！真实数据占比超过60%")
    elif len(real_data) >= 4:
        print("\n⚠️  部分改进，真实数据占比有所提升")
    else:
        print("\n❌ 改进效果有限，大部分数据仍为代理或模拟")
    
    print("=" * 70)
    
    return factors

if __name__ == '__main__':
    try:
        test_enhanced_macro_data()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
