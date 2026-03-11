#!/usr/bin/env python3
"""
黄金价格预测Web应用启动脚本
自动寻找可用端口
"""
import socket
import sys

def find_free_port(start_port=8080, max_port=9000):
    """寻找可用端口"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

if __name__ == '__main__':
    port = find_free_port()
    if port is None:
        print("❌ 无法找到可用端口")
        sys.exit(1)
    
    # 导入并启动应用
    from gold_app import app
    
    print("=" * 70)
    print("📊 黄金价格宏观预测系统")
    print("=" * 70)
    print(f"\n🥇 当日价格数据源: 上海期货交易所 (SHFE)")
    print(f"   合约: AU2506 / AU2504 / AU2412")
    print(f"   单位: 元/克 (CNY/g)")
    print(f"\n📍 服务端口: {port}")
    print(f"🌐 本地访问: http://127.0.0.1:{port}")
    print(f"🌐 网络访问: http://0.0.0.0:{port}")
    print("\n📈 宏观因子数据源:")
    print("  ✅ 美元指数 (DXY) - Yahoo Finance")
    print("  ✅ 实际利率 (TIPS) - TIPS ETF")
    print("  ✅ 通胀预期 (CPI) - akshare 美国/中国CPI")
    print("  ✅ 美债收益率 - Yahoo Finance")
    print("  ✅ VIX波动率 - Yahoo Finance")
    print("  ✅ 金银比/铜金比 - akshare 上期所")
    print("  ⚠️  地缘政治风险 - VIX代理")
    print("  ⚠️  经济不确定性 - 波动率代理")
    print("  ⚠️  黄金ETF持仓 - 华安ETF代理")
    print("\n🔗 API端点:")
    print(f"  • 黄金价格: http://127.0.0.1:{port}/api/data")
    print(f"  • 宏观因子: http://127.0.0.1:{port}/api/macro-factors")
    print(f"  • 数据质量: http://127.0.0.1:{port}/api/data-quality")
    print("=" * 70)
    print(f"🚀 正在启动服务...")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=port)
