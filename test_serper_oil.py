#!/usr/bin/env python3
"""
测试 Serper API 获取原油价格
"""

import os
import requests
import json
import re

def serper_search(query):
    """使用 Serper API 搜索"""
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("❌ 请先设置 SERPER_API_KEY 环境变量")
        print("   export SERPER_API_KEY=your_api_key")
        return None
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "us", "hl": "zh-cn"})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"\n🔍 搜索: {query}")
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 搜索成功!")
            
            # 显示 answerBox
            if 'answerBox' in data:
                print("\n📦 AnswerBox:")
                print(json.dumps(data['answerBox'], indent=2, ensure_ascii=False))
            
            # 显示前3条结果
            if 'organic' in data:
                print("\n📋 前3条搜索结果:")
                for i, item in enumerate(data['organic'][:3], 1):
                    print(f"\n  [{i}] {item.get('title', 'N/A')}")
                    print(f"      {item.get('snippet', 'N/A')[:100]}...")
            
            return data
        else:
            print(f"❌ API 请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def extract_price(text):
    """从文本提取价格"""
    patterns = [
        r'\$([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*USD',
        r'([\d,]+\.?\d*)\s*美元',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
    return None

def extract_change(text):
    """从文本提取涨跌"""
    match = re.search(r'([\+\-]\d+\.?\d*)%', text)
    if match:
        try:
            return float(match.group(1))
        except:
            pass
    return None

def test_oil_prices():
    """测试获取原油价格"""
    print("="*60)
    print("🛢️  使用 Serper API 获取原油价格测试")
    print("="*60)
    
    # 测试 WTI
    result = serper_search("WTI crude oil price today")
    if result:
        print("\n" + "-"*40)
        print("💰 尝试提取 WTI 价格...")
        
        # 从 answerBox 提取
        if 'answerBox' in result:
            answer = result['answerBox'].get('answer', '')
            snippet = result['answerBox'].get('snippet', '')
            combined = answer + ' ' + snippet
            
            price = extract_price(combined)
            change = extract_change(combined)
            
            if price:
                print(f"✅ WTI 价格: ${price:.2f}")
                if change:
                    print(f"   涨跌: {change:+.2f}%")
            else:
                print("⚠️ 无法从 answerBox 提取价格")
        
        # 从搜索结果提取
        if 'organic' in result:
            for item in result['organic'][:2]:
                text = item.get('title', '') + ' ' + item.get('snippet', '')
                price = extract_price(text)
                if price:
                    print(f"✅ 从搜索结果提取价格: ${price:.2f}")
                    break
    
    # 测试布伦特
    print("\n" + "="*60)
    result = serper_search("Brent crude oil price today")
    if result:
        print("\n" + "-"*40)
        print("💰 尝试提取布伦特价格...")
        
        if 'answerBox' in result:
            answer = result['answerBox'].get('answer', '')
            snippet = result['answerBox'].get('snippet', '')
            combined = answer + ' ' + snippet
            
            price = extract_price(combined)
            change = extract_change(combined)
            
            if price:
                print(f"✅ 布伦特价格: ${price:.2f}")
                if change:
                    print(f"   涨跌: {change:+.2f}%")

if __name__ == '__main__':
    # 尝试从 .env 文件加载
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    test_oil_prices()
