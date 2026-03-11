#!/bin/bash
# 添加原油定时任务到 crontab

echo "⛽ 添加原油每日推送定时任务..."

# 创建临时文件
crontab -l > /tmp/current_crontab.txt 2>/dev/null || echo "# 新建 crontab" > /tmp/current_crontab.txt

# 检查是否已存在原油任务
if grep -q "oil_daily_push.py" /tmp/current_crontab.txt; then
    echo "⚠️ 原油推送任务已存在，跳过添加"
else
    # 添加原油推送任务
    # 7:35 - 在 WTI/Brent 价格推送后，发送综合报告
    cat >> /tmp/current_crontab.txt << 'EOF'

# ===== 原油推送任务 =====
# 7:35 - 原油每日综合推送（在单独WTI/Brent报价后）
35 7 * * * cd /Users/ydy/CodeBuddy/20260310193311 && /opt/anaconda3/bin/python3 oil_daily_push.py >> /tmp/oil_push.log 2>&1
EOF
    
    # 应用新的 crontab
    crontab /tmp/current_crontab.txt
    echo "✅ 原油推送任务已添加！"
fi

# 显示当前所有与油价相关的任务
echo ""
echo "📋 当前所有油价相关定时任务："
crontab -l | grep -E "(oil|原油|WTI|Brent)"

echo ""
echo "📊 完整的定时任务列表："
crontab -l

# 清理临时文件
rm -f /tmp/current_crontab.txt

echo ""
echo "✨ 完成！"
