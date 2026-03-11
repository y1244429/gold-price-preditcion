#!/usr/bin/env python3
"""
检查宏观因子数据真实度
区分真实数据、代理数据、模拟数据
"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

def check_data_realism():
    from gold_app import MacroFactorCollector
    
    collector = MacroFactorCollector()
    factors = collector.get_all_factors()
    
    print('='*70)
    print('📊 宏观因子数据真实度检查报告')
    print('='*70)
    
    real_data = []
    proxy_data = []
    mock_data = []
    
    for name, data in factors.items():
        source = data.get('data_source', '未知')
        reliability = data.get('reliability', '低')
        
        if '模拟' in source or '备用' in source or reliability == '低':
            mock_data.append((name, data))
        elif '代理' in source or reliability == '中':
            proxy_data.append((name, data))
        else:
            real_data.append((name, data))
    
    # 真实数据
    print(f'\n✅ 真实数据 ({len(real_data)}个):')
    for name, data in real_data:
        value = data.get('value')
        if isinstance(value, dict):
            value_str = f"金/银比: {value.get('gold_silver', 'N/A')}"
        else:
            value_str = f'{value}'
        print(f'  • {name}: {value_str}')
        print(f'    来源: {data.get("data_source", "未知")} ({data.get("reliability", "低")})')
        if data.get('method'):
            print(f'    方法: {data.get("method")}')
    
    # 代理数据
    print(f'\n⚠️  代理数据 ({len(proxy_data)}个):')
    for name, data in proxy_data:
        value = data.get('value')
        print(f'  • {name}: {value}')
        print(f'    来源: {data.get("data_source", "未知")} ({data.get("reliability", "低")})')
        if data.get('note'):
            print(f'    说明: {data.get("note")}')
    
    # 模拟数据
    print(f'\n❌ 模拟数据 ({len(mock_data)}个):')
    for name, data in mock_data:
        value = data.get('value')
        print(f'  • {name}: {value}')
        print(f'    来源: {data.get("data_source", "未知")} ({data.get("reliability", "低")})')
        if data.get('error'):
            print(f'    错误: {data.get("error")[:50]}')
    
    print('\n' + '='*70)
    print(f'📈 真实度统计:')
    print(f'   ✅ 高真实度: {len(real_data)}/9 ({len(real_data)*100//9}%)')
    print(f'   ⚠️  代理数据: {len(proxy_data)}/9 ({len(proxy_data)*100//9}%)')
    print(f'   ❌ 模拟数据: {len(mock_data)}/9 ({len(mock_data)*100//9}%)')
    print('='*70)
    
    # 改进建议
    if len(mock_data) > 0 or len(proxy_data) > 0:
        print('\n💡 改进建议:')
        if any('GPR' in name for name, _ in proxy_data):
            print('   • 地缘政治风险: 爬取 Caldara-Iacoviello GPR 指数')
        if any('ETF' in name for name, _ in proxy_data + mock_data):
            print('   • ETF持仓: 爬取 SPDR Gold Shares 官方持仓')
        if any('EPU' in name or '不确定' in name for name, _ in proxy_data):
            print('   • 经济不确定性: 使用 Baker et al. EPU 指数')
        print('='*70)

if __name__ == '__main__':
    check_data_realism()
