#!/usr/bin/env python3
"""检查API状态并获取数据质量报告"""
import requests
import json

try:
    response = requests.get('http://127.0.0.1:8080/api/data-quality', timeout=10)
    if response.status_code == 200:
        data = response.json()
        print("="*70)
        print("📊 宏观因子数据质量报告")
        print("="*70)
        
        print(f"\n✅ 高真实度数据 ({len(data['high_reliability'])}个):")
        for item in data['high_reliability']:
            print(f"  • {item['name']}")
            print(f"    来源: {item['source']}")
            if item.get('method'):
                print(f"    方法: {item['method']}")
            print(f"    数值: {item['value']}")
        
        print(f"\n⚠️  中等真实度数据 ({len(data['medium_reliability'])}个):")
        for item in data['medium_reliability']:
            print(f"  • {item['name']}")
            print(f"    来源: {item['source']}")
            if item.get('note'):
                print(f"    说明: {item['note']}")
        
        print(f"\n❌ 低真实度数据 ({len(data['low_reliability'])}个):")
        for item in data['low_reliability']:
            print(f"  • {item['name']}")
            print(f"    来源: {item['source']}")
        
        print("\n" + "="*70)
    else:
        print(f"❌ API返回错误: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到应用")
    print("   请先启动应用: python gold_app.py")
except Exception as e:
    print(f"❌ 错误: {e}")
