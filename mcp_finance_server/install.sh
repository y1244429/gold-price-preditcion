#!/bin/bash

echo "=============================================="
echo "🚀 金融数据 MCP 服务器安装脚本"
echo "=============================================="

# 检查Python版本
echo ""
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "Python版本: $python_version"

# 安装依赖
echo ""
echo "📦 安装依赖包..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功!"
else
    echo "❌ 依赖安装失败，请检查网络连接"
    exit 1
fi

# 测试服务器
echo ""
echo "🧪 测试服务器..."
python test_server.py

echo ""
echo "=============================================="
echo "✨ 安装完成!"
echo "=============================================="
echo ""
echo "使用方法:"
echo "1. 直接运行: python server.py"
echo "2. 在 Claude Desktop 中添加 mcp_config.json 配置"
echo "3. 或者在 CodeBuddy 中配置该 MCP 服务器"
echo ""
