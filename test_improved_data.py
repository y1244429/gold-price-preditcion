#!/usr/bin/env python3
"""测试改进后的宏观数据获取"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

print('=' * 70)
print('📊 改进后的宏观数据获取测试')
print('=' * 70)

from gold_app import MacroFactorCollector
collector = MacroFactorCollector()

real_count = 0
proxy_count = 0
mock_count = 0

factors_to_test = ['美元指数', '通胀预期', '地缘政治风险', '经济不确定性']
methods = {
    '美元指数': collector.get_dxy,
    '通胀预期': collector.get_inflation_cpi,
    '地缘政治风险': collector.get_gpr,
    '经济不确定性': collector.get_epu,
}

for name, method in methods.items():
    print(f'\n🔍 测试 {name}...')
    try:
        result = method()
        source = result.get('data_source', '未知')
        reliability = result.get('reliability', '低')
        value = result.get('value')
        
        if '备用' in source or '失败' in source or reliability == '低':
            mock_count += 1
            status = '❌ 模拟'
        elif '代理' in source or '估算' in source or reliability == '中':
            proxy_count += 1
            status = '⚠️  代理'
        else:
            real_count += 1
            status = '✅ 真实'
        
        print(f'   {status} {name}')
        print(f'   值: {value}')
        print(f'   来源: {source}')
        print(f'   可信度: {reliability}')
    except Exception as e:
        print(f'   ❌ 失败: {e}')
        mock_count += 1

print('\n' + '=' * 70)
print('📊 统计')
print('=' * 70)
total = real_count + proxy_count + mock_count
print(f'✅ 真实数据: {real_count}/{total}')
print(f'⚠️  代理数据: {proxy_count}/{total}')
print(f'❌ 模拟数据: {mock_count}/{total}')
print('=' * 70)
