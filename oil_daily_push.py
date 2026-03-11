#!/usr/bin/env python3
"""
原油每日推送脚本
获取 WTI 和布伦特原油价格，推送到微信/邮件
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_oil_prices():
    """获取原油价格数据"""
    data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "wti": None,
        "brent": None
    }
    
    try:
        # WTI 原油 (CL=F)
        wti = yf.Ticker("CL=F")
        wti_hist = wti.history(period="5d")
        if not wti_hist.empty:
            current = wti_hist['Close'].iloc[-1]
            prev = wti_hist['Close'].iloc[-2]
            change = current - prev
            change_pct = (change / prev) * 100
            
            data["wti"] = {
                "name": "WTI原油",
                "symbol": "CL=F",
                "price": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": "USD/桶",
                "trend": "📈上涨" if change > 0 else "📉下跌" if change < 0 else "➡️持平"
            }
    except Exception as e:
        print(f"❌ WTI获取失败: {e}")
    
    try:
        # 布伦特原油 (BZ=F)
        brent = yf.Ticker("BZ=F")
        brent_hist = brent.history(period="5d")
        if not brent_hist.empty:
            current = brent_hist['Close'].iloc[-1]
            prev = brent_hist['Close'].iloc[-2]
            change = current - prev
            change_pct = (change / prev) * 100
            
            data["brent"] = {
                "name": "布伦特原油",
                "symbol": "BZ=F",
                "price": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": "USD/桶",
                "trend": "📈上涨" if change > 0 else "📉下跌" if change < 0 else "➡️持平"
            }
    except Exception as e:
        print(f"❌ 布伦特获取失败: {e}")
    
    return data

def format_push_message(data):
    """格式化推送消息"""
    wti = data.get("wti")
    brent = data.get("brent")
    
    if not wti and not brent:
        return None
    
    message = f"""
⛽ 原油市场日报 | {data['update_time'][:10]}

{"="*30}

"""
    
    if wti:
        message += f"""📊 {wti['name']} ({wti['symbol']})
   💵 价格: {wti['price']} {wti['currency']}
   {wti['trend']} {wti['change']:+.2f} ({wti['change_pct']:+.2f}%)

"""
    
    if brent:
        message += f"""📊 {brent['name']} ({brent['symbol']})
   💵 价格: {brent['price']} {brent['currency']}
   {brent['trend']} {brent['change']:+.2f} ({brent['change_pct']:+.2f}%)

"""
    
    # 计算价差
    if wti and brent:
        spread = brent['price'] - wti['price']
        message += f"""📈 价差分析
   布伦特惠差: {spread:.2f} USD/桶
   {'⚠️ 价差扩大' if abs(spread) > 5 else '✅ 价差正常'}

"""
    
    message += f"""
💡 市场影响
   • WTI上涨 → 通胀预期升温 → 利好黄金
   • 原油上涨 → 铜等大宗商品联动
   
{"="*30}
📱 数据来源: Yahoo Finance
"""
    
    return message

def save_to_json(data, filename="oil_data.json"):
    """保存数据到JSON"""
    try:
        # 读取现有数据
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        # 添加新数据
        history.append(data)
        
        # 只保留最近30天
        history = history[-30:]
        
        # 保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存到 {filename}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def main():
    """主函数"""
    print("="*50)
    print("⛽ 原油每日推送脚本")
    print("="*50)
    
    # 获取数据
    print("\n📊 正在获取原油价格...")
    data = get_oil_prices()
    
    # 格式化消息
    message = format_push_message(data)
    
    if message:
        print("\n" + message)
        
        # 保存到文件
        save_to_json(data, "/Users/ydy/CodeBuddy/20260310193311/data_cache/oil_daily.json")
        
        # 输出到标准输出（可用于管道传递）
        print("\n📤 推送消息已生成")
        
        # 这里可以添加微信/邮件推送逻辑
        # send_wechat(message)
        # send_email(message)
        
    else:
        print("❌ 未能获取原油价格数据")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
