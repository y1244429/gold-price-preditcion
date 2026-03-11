#!/usr/bin/env python3
"""
测试 Serper API 是否配置正确
"""

import os
import requests
import json

def test_serper_api():
    """测试 Serper API"""
    api_key = os.getenv('SERPER_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        print("❌ 错误: 请先设置 SERPER_API_KEY 环境变量")
        print("   方法1: export SERPER_API_KEY=your_api_key")
        print("   方法2: 将 API Key 写入 .env 文件")
        return False
    
    print("🧪 测试 Serper API 连接...")
    print(f"   API Key: {api_key[:10]}...")
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": "黄金价格"})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Serper API 连接成功!")
            print(f"   搜索结果数: {len(data.get('organic', []))}")
            return True
        else:
            print(f"❌ API 请求失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    # 尝试从 .env 文件加载
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    success = test_serper_api()
    
    if not success:
        print("\n📖 获取 API Key 步骤:")
        print("   1. 访问 https://serper.dev")
        print("   2. 注册账号（免费额度：2500次/月）")
        print("   3. 进入 Dashboard 获取 API Key")
        print("   4. 设置环境变量: export SERPER_API_KEY=your_key")
