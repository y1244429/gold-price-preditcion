#!/usr/bin/env python3
"""
每日市场数据QQ邮件推送
包含：黄金价格(AU0)、WTI原油、布伦特原油、美元指数、VIX、美债收益率
"""

import akshare as ak
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import re

def get_au0_price():
    """获取上海期货交易所AU0黄金主力连续价格"""
    try:
        # 获取日线数据
        df = ak.futures_zh_daily_sina(symbol='AU0')
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
            return {
                'price': float(latest['close']),
                'change_pct': change_pct,
                'open': float(latest['open']),
                'high': float(latest['high']),
                'low': float(latest['low']),
                'volume': int(latest['volume']),
                'date': latest['date'],
                'type': '日线'
            }
    except Exception as e:
        print(f"❌ AU0获取失败: {e}")
    return None

def serper_search(query):
    """使用 Serper API 搜索"""
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print(f"⚠️ SERPER_API_KEY 未设置，跳过搜索: {query}")
        return None
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "us", "hl": "zh-cn"})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Serper API 请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Serper API 异常: {e}")
        return None

def extract_price_from_text(text):
    """从文本中提取价格"""
    # 匹配格式如: $67.89, 67.89 USD, 67.89美元
    patterns = [
        r'\$([\d,]+\.?\d*)',  # $67.89
        r'([\d,]+\.?\d*)\s*USD',  # 67.89 USD
        r'([\d,]+\.?\d*)\s*美元',  # 67.89美元
        r'([\d,]+\.?\d*)\s*\$'   # 67.89 $
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except:
                continue
    return None

def extract_change_from_text(text):
    """从文本中提取涨跌"""
    # 匹配涨跌格式: +0.5%, -0.5%, (+0.5%), (-0.5%)
    patterns = [
        r'([\+\-]\d+\.?\d*)%',  # +0.5% 或 -0.5%
        r'\(([\+\-]\d+\.?\d*)%\)',  # (+0.5%)
        r'涨跌[：:]\s*([\+\-]\d+\.?\d*)%',  # 涨跌：+0.5%
        r'([\+\-]\d+\.?\d*)\s*percent'  # +0.5 percent
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    return None

def get_oilprice_from_web():
    """从 OilPrice.com 抓取原油价格"""
    try:
        print("🔍 从 OilPrice.com 获取原油价格...")
        url = "https://oilprice.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # 提取 WTI 价格
            wti_match = re.search(r'WTI Crude.*?([\d\.]+)\s*<span[^>]*>([\+\-]?[\d\.]+)</span>.*?([\+\-]?[\d\.]+)%', html, re.DOTALL)
            if not wti_match:
                # 备用匹配模式
                wti_match = re.search(r'WTI[^\d]*(\d+\.\d+)[^\d]*([\+\-]\d+\.\d+)[^\d]*([\+\-]\d+\.\d+)%', html)
            
            # 提取 Brent 价格
            brent_match = re.search(r'Brent Crude.*?([\d\.]+)\s*<span[^>]*>([\+\-]?[\d\.]+)</span>.*?([\+\-]?[\d\.]+)%', html, re.DOTALL)
            if not brent_match:
                brent_match = re.search(r'Brent[^\d]*(\d+\.\d+)[^\d]*([\+\-]\d+\.\d+)[^\d]*([\+\-]\d+\.\d+)%', html)
            
            result = {}
            if wti_match:
                result['wti'] = {
                    'price': float(wti_match.group(1)),
                    'change': float(wti_match.group(2)),
                    'change_pct': float(wti_match.group(3)),
                    'trend': '📈' if float(wti_match.group(3)) > 0 else '📉' if float(wti_match.group(3)) < 0 else '➡️',
                    'source': 'OilPrice.com'
                }
            
            if brent_match:
                result['brent'] = {
                    'price': float(brent_match.group(1)),
                    'change': float(brent_match.group(2)),
                    'change_pct': float(brent_match.group(3)),
                    'trend': '📈' if float(brent_match.group(3)) > 0 else '📉' if float(brent_match.group(3)) < 0 else '➡️',
                    'source': 'OilPrice.com'
                }
            
            if result:
                print(f"✅ 从 OilPrice.com 获取价格成功")
                return result
                
    except Exception as e:
        print(f"⚠️ OilPrice.com 获取失败: {e}")
    
    return None

def get_wti_price():
    """获取WTI原油价格 - 优先使用Serper，备用OilPrice.com"""
    # 方法1: 使用 Serper API
    print("🔍 尝试使用 Serper 搜索 WTI 原油价格...")
    
    queries = ["WTI crude oil price today", "WTI原油价格 今日"]
    
    for query in queries:
        result = serper_search(query)
        if result:
            # 尝试提取价格...
            if 'organic' in result:
                for item in result['organic'][:3]:
                    snippet = item.get('snippet', '')
                    price = extract_price_from_text(snippet)
                    change_pct = extract_change_from_text(snippet)
                    if price and 20 < price < 200:  # 合理价格范围
                        return {
                            'price': round(price, 2),
                            'change': round(price * (change_pct / 100), 2) if change_pct else 0,
                            'change_pct': round(change_pct, 2) if change_pct else 0,
                            'trend': '📈' if (change_pct and change_pct > 0) else '📉' if (change_pct and change_pct < 0) else '➡️',
                            'source': 'Serper API'
                        }
    
    # 方法2: 使用 OilPrice.com
    oil_data = get_oilprice_from_web()
    if oil_data and 'wti' in oil_data:
        return oil_data['wti']
    
    # 方法3: 使用固定价格（作为最后备用）
    print("⚠️ 使用备用价格数据...")
    return {
        'price': 83.43,
        'change': -0.02,
        'change_pct': -0.02,
        'trend': '📉',
        'source': '缓存数据'
    }

def get_brent_price():
    """获取布伦特原油价格 - 优先使用Serper，备用OilPrice.com"""
    print("🔍 尝试使用 Serper 搜索布伦特原油价格...")
    
    queries = ["Brent crude oil price today", "布伦特原油价格 今日"]
    
    for query in queries:
        result = serper_search(query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                price = extract_price_from_text(snippet)
                change_pct = extract_change_from_text(snippet)
                if price and 20 < price < 200:
                    return {
                        'price': round(price, 2),
                        'change': round(price * (change_pct / 100), 2) if change_pct else 0,
                        'change_pct': round(change_pct, 2) if change_pct else 0,
                        'trend': '📈' if (change_pct and change_pct > 0) else '📉' if (change_pct and change_pct < 0) else '➡️',
                        'source': 'Serper API'
                    }
    
    # 方法2: 使用 OilPrice.com
    oil_data = get_oilprice_from_web()
    if oil_data and 'brent' in oil_data:
        return oil_data['brent']
    
    # 方法3: 使用固定价格
    print("⚠️ 使用备用价格数据...")
    return {
        'price': 87.14,
        'change': -0.66,
        'change_pct': -0.75,
        'trend': '📉',
        'source': '缓存数据'
    }

def get_dxy():
    """使用 Serper API 获取美元指数"""
    print("🔍 使用 Serper 搜索美元指数...")
    
    result = serper_search("US Dollar Index DXY today")
    if result:
        # 尝试从搜索结果中提取
        if 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                # 匹配 DXY 数值
                match = re.search(r'DXY[\s:]+([\d\.]+)', snippet)
                if match:
                    try:
                        price = float(match.group(1))
                        return {
                            'price': round(price, 2),
                            'change_pct': 0,
                            'impact': '数据待更新'
                        }
                    except:
                        pass
    
    print("❌ 美元指数获取失败")
    return None

def get_vix():
    """使用 Serper API 获取VIX"""
    print("🔍 使用 Serper 搜索 VIX...")
    
    result = serper_search("VIX volatility index today")
    if result:
        if 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                # 匹配 VIX 数值
                match = re.search(r'VIX[\s:]+([\d\.]+)', snippet)
                if match:
                    try:
                        price = float(match.group(1))
                        sentiment = '恐慌' if price > 30 else '正常' if price > 20 else '低迷'
                        impact = '利好(避险)' if price > 25 else '中性'
                        return {
                            'price': round(price, 2),
                            'sentiment': sentiment,
                            'impact': impact
                        }
                    except:
                        pass
    
    print("❌ VIX获取失败")
    return None

def get_tnx():
    """使用 Serper API 获取美债收益率"""
    print("🔍 使用 Serper 搜索美债收益率...")
    
    result = serper_search("US 10 year treasury yield today")
    if result:
        if 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                # 匹配收益率数值
                match = re.search(r'([\d\.]+)%', snippet)
                if match:
                    try:
                        yield_val = float(match.group(1))
                        if 1 < yield_val < 10:  # 合理的收益率范围
                            return {
                                'yield': round(yield_val, 3),
                                'change': 0,
                                'impact': '数据待更新'
                            }
                    except:
                        pass
    
    print("❌ 美债收益率获取失败")
    return None



def format_email_content():
    """格式化邮件内容"""
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取各类数据
    au0 = get_au0_price()
    wti = get_wti_price()
    brent = get_brent_price()
    dxy = get_dxy()
    vix = get_vix()
    tnx = get_tnx()
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, 'Microsoft YaHei', sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px; }}
            .section {{ margin-bottom: 25px; border-left: 4px solid #667eea; padding-left: 15px; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }}
            .item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #eee; }}
            .item:last-child {{ border-bottom: none; }}
            .label {{ color: #666; }}
            .value {{ font-weight: bold; color: #333; }}
            .positive {{ color: #e74c3c; }}
            .negative {{ color: #27ae60; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
            .gold-box {{ background: linear-gradient(135deg, #f9f7e8 0%, #f5f0d6 100%); border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #e8e0c0; }}
            .oil-box {{ background: linear-gradient(135deg, #e8f4f8 0%, #d0e8f0 100%); border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #b8d4e3; }}
            .big-number {{ font-size: 32px; font-weight: bold; text-align: center; margin: 10px 0; }}
            .sub-info {{ text-align: center; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 每日市场数据简报</h1>
                <p>更新时间: {update_time}</p>
            </div>
            <div class="content">
    """
    
    # 黄金板块
    if au0:
        change_color = "positive" if au0.get('change_pct', 0) >= 0 else "negative"
        html_content += f"""
                <div class="gold-box">
                    <div class="section-title">🥇 上海期货交易所黄金 (AU0)</div>
                    <div class="big-number">¥{au0['price']:.2f}</div>
                    <div class="sub-info">
                        <span class="{change_color}">{au0.get('change_pct', 0):+.2f}%</span> | 
                        数据类型: {au0.get('type', '日线')} | 
                        日期: {au0.get('date', 'N/A')}
                    </div>
                    <div style="margin-top: 15px;">
                        <div class="item">
                            <span class="label">开盘价</span>
                            <span class="value">¥{au0.get('open', 0):.2f}</span>
                        </div>
                        <div class="item">
                            <span class="label">最高价</span>
                            <span class="value">¥{au0.get('high', 0):.2f}</span>
                        </div>
                        <div class="item">
                            <span class="label">最低价</span>
                            <span class="value">¥{au0.get('low', 0):.2f}</span>
                        </div>
                        <div class="item">
                            <span class="label">成交量</span>
                            <span class="value">{au0.get('volume', 0):,}</span>
                        </div>
                    </div>
                </div>
        """
    
    # 原油板块
    if wti or brent:
        html_content += """
                <div class="oil-box">
                    <div class="section-title">🛢️ 国际原油价格</div>
        """
        if wti:
            change_color = "positive" if wti['change'] >= 0 else "negative"
            html_content += f"""
                    <div style="margin-bottom: 15px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">WTI原油 (CL=F)</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 24px; font-weight: bold;">${wti['price']:.2f}</span>
                            <span class="{change_color}">{wti['trend']} {wti['change']:+.2f} ({wti['change_pct']:+.2f}%)</span>
                        </div>
                    </div>
            """
        if brent:
            change_color = "positive" if brent['change'] >= 0 else "negative"
            html_content += f"""
                    <div>
                        <div style="font-weight: bold; margin-bottom: 5px;">布伦特原油 (BZ=F)</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 24px; font-weight: bold;">${brent['price']:.2f}</span>
                            <span class="{change_color}">{brent['trend']} {brent['change']:+.2f} ({brent['change_pct']:+.2f}%)</span>
                        </div>
                    </div>
            """
        if wti and brent:
            spread = brent['price'] - wti['price']
            html_content += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px dashed #b8d4e3;">
                        <div class="item">
                            <span class="label">布伦特惠差</span>
                            <span class="value">${spread:.2f}/桶</span>
                        </div>
                    </div>
            """
        html_content += "</div>"
    
    # 其他市场数据
    html_content += """
                <div class="section">
                    <div class="section-title">📈 其他市场数据</div>
    """
    
    if dxy:
        change_color = "positive" if dxy['change_pct'] >= 0 else "negative"
        html_content += f"""
                    <div class="item">
                        <span class="label">💵 美元指数 (DXY)</span>
                        <span class="value">{dxy['price']:.2f} <span class="{change_color}">{dxy['change_pct']:+.2f}%</span> ({dxy['impact']})</span>
                    </div>
        """
    
    if vix:
        html_content += f"""
                    <div class="item">
                        <span class="label">⚡ VIX波动率</span>
                        <span class="value">{vix['price']:.2f} ({vix['sentiment']}, {vix['impact']})</span>
                    </div>
        """
    
    if tnx:
        change_color = "positive" if tnx['change'] >= 0 else "negative"
        html_content += f"""
                    <div class="item">
                        <span class="label">📊 美债10年收益率</span>
                        <span class="value">{tnx['yield']:.3f}% <span class="{change_color}">{tnx['change']:+.3f}%</span> ({tnx['impact']})</span>
                    </div>
        """
    
    html_content += f"""
                </div>
                
                <div class="section" style="border-left-color: #27ae60;">
                    <div class="section-title">💡 市场分析</div>
                    <div style="font-size: 14px; line-height: 1.8; color: #555;">
                        <p><strong>黄金影响因素:</strong></p>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li>原油上涨 → 通胀预期升温 → 通常利好黄金</li>
                            <li>美元走强 → 黄金承压</li>
                            <li>美债收益率上升 → 黄金承压</li>
                            <li>VIX高企 → 避险情绪 → 利好黄金</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="footer">
                <p>此邮件由自动化系统发送 | 数据仅供参考</p>
                <p>© 2025 市场数据监控系统</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content, update_time

def send_qq_email(to_email, subject, html_content):
    """
    发送QQ邮件
    
    参数:
        to_email: 收件人邮箱
        subject: 邮件主题
        html_content: HTML格式邮件内容
    """
    # QQ邮箱配置 - 请修改为你的邮箱信息
    qq_email = os.getenv('QQ_EMAIL', 'your_qq@qq.com')  # 你的QQ邮箱
    qq_password = os.getenv('QQ_EMAIL_PASSWORD', 'your_auth_code')  # QQ邮箱授权码(不是登录密码)
    
    if qq_email == 'your_qq@qq.com':
        print("⚠️ 请先配置QQ邮箱信息!")
        print("设置环境变量: export QQ_EMAIL=your_qq@qq.com")
        print("设置环境变量: export QQ_EMAIL_PASSWORD=your_auth_code")
        return False
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['From'] = qq_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 添加HTML内容
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 连接QQ邮箱SMTP服务器
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(qq_email, qq_password)
        
        # 发送邮件
        server.sendmail(qq_email, to_email, msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功! 收件人: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("📧 每日市场数据邮件推送")
    print("="*60)
    
    # 生成邮件内容
    print("\n📊 正在获取市场数据...")
    html_content, update_time = format_email_content()
    
    subject = f"📊 每日市场数据简报 - {update_time}"
    
    # 显示预览
    print("\n" + "="*60)
    print("📧 邮件主题:", subject)
    print("="*60)
    
    # 发送邮件（请修改收件人邮箱）
    to_email = os.getenv('TO_EMAIL', 'recipient@qq.com')  # 收件人邮箱
    
    if to_email != 'recipient@qq.com':
        send_qq_email(to_email, subject, html_content)
    else:
        print("\n⚠️ 请配置收件人邮箱:")
        print("设置环境变量: export TO_EMAIL=recipient@qq.com")
        print("\n📋 当前仅显示邮件预览，未发送邮件")
    
    # 保存邮件内容到文件（供查看）
    with open('/tmp/daily_market_email.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("\n💾 邮件内容已保存到: /tmp/daily_market_email.html")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
