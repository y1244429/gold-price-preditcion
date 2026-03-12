#!/usr/bin/env python3
"""
快速测试 Web Search 获取铜价宏观数据
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('.env')

print("=" * 70)
print("🧪 Web Search API 测试")
print("=" * 70)

# 检查 API Keys
serper_key = os.getenv('SERPER_API_KEY')
tavily_key = os.getenv('TAVILY_API_KEY')

print(f"\n📋 API Key 状态:")
print(f"  • Serper API: {'✅ 已设置' if serper_key else '❌ 未设置'}")
print(f"  • Tavily API: {'✅ 已设置' if tavily_key else '❌ 未设置'}")

if not serper_key and not tavily_key:
    print("\n❌ 错误: 未设置任何 API Key")
    exit(1)

# 导入并测试
from copper_macro_web_search import CopperMacroWebSearch

searcher = CopperMacroWebSearch()

# 测试搜索中国 PMI
print("\n🔍 测试1: 搜索中国 PMI...")
result = searcher.search_with_serper("中国制造业PMI 2025年2月 国家统计局", num_results=3)
if result and 'organic' in result:
    print(f"  ✅ 找到 {len(result['organic'])} 条结果")
    for i, item in enumerate(result['organic'][:2], 1):
        print(f"    {i}. {item.get('title', '')[:50]}...")
        print(f"       {item.get('snippet', '')[:80]}...")
else:
    print("  ❌ 搜索失败")

# 测试搜索铜 TC/RC
print("\n🔍 测试2: 搜索铜 TC/RC...")
result = searcher.search_with_serper("铜精矿 TC RC 加工费 2025", num_results=3)
if result and 'organic' in result:
    print(f"  ✅ 找到 {len(result['organic'])} 条结果")
    for i, item in enumerate(result['organic'][:2], 1):
        print(f"    {i}. {item.get('title', '')[:50]}...")
else:
    print("  ❌ 搜索失败")

# 获取所有宏观数据
print("\n" + "=" * 70)
print("📊 获取完整宏观数据...")
print("=" * 70)

data = searcher.get_all_web_data()

print("\n📋 获取到的数据:")
for key, value in data.items():
    print(f"  • {key}: {value}")

print("\n" + "=" * 70)
print("✅ 测试完成")
print("=" * 70)
