#!/usr/bin/env python3
"""
铜价预测增强版 Web 应用
基于 copper_prediction_enhanced.py - 集成四层宏观因子
"""
from flask import Flask, render_template_string, jsonify
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
import sys
import os

warnings.filterwarnings('ignore')

app = Flask(__name__)

# 导入增强版铜价预测
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

from copper_prediction import get_copper_data, calculate_indicators
from copper_prediction_enhanced import EnhancedCopperPredictor
from copper_macro_factors import get_default_macro_data

def convert_to_serializable(obj):
    """转换 numpy 类型为 Python 原生类型"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    return obj

def run_enhanced_prediction():
    """运行增强版铜价预测"""
    try:
        predictor = EnhancedCopperPredictor()
        
        # 使用默认宏观数据
        macro_data = get_default_macro_data()
        
        # 运行预测
        result = predictor.predict(
            macro_data=macro_data,
            use_macro_adjustment=True,
            use_risk_management=True
        )
        
        return convert_to_serializable(result)
    except Exception as e:
        return {'error': str(e)}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔶 铜价预测 - 增强版</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,165,0,0.3);
            margin-bottom: 30px;
        }
        h1 {
            font-size: 32px;
            background: linear-gradient(135deg, #FFD700, #FF6347);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 14px; }
        
        .price-card {
            background: linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,99,71,0.05));
            border: 2px solid rgba(255,165,0,0.4);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
        }
        .price-label { color: #aaa; font-size: 16px; text-transform: uppercase; letter-spacing: 2px; }
        .price-value {
            font-size: 56px;
            font-weight: bold;
            color: #FFD700;
            margin: 15px 0;
            text-shadow: 0 0 30px rgba(255,215,0,0.3);
        }
        .price-change { font-size: 24px; margin-top: 10px; }
        .up { color: #00d084; }
        .down { color: #ff4757; }
        
        .btn {
            background: linear-gradient(135deg, #FFD700, #FF6347);
            color: #000;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            margin: 10px;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(255,215,0,0.4); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .results { display: none; }
        .result-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .result-title { 
            color: #FFD700; 
            font-size: 20px; 
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .prediction-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .prediction-box {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .prediction-box.highlight {
            border: 2px solid #FFD700;
            background: rgba(255,215,0,0.1);
        }
        .box-label { color: #888; font-size: 14px; margin-bottom: 10px; }
        .box-value { font-size: 28px; font-weight: bold; color: #fff; }
        .box-change { font-size: 16px; margin-top: 8px; }
        
        .macro-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
        }
        .macro-card {
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 15px;
        }
        .macro-title { color: #FFD700; font-size: 14px; margin-bottom: 10px; }
        .macro-item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 13px;
        }
        .macro-item:last-child { border-bottom: none; }
        
        .risk-bar {
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .risk-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        .risk-low { background: #00d084; }
        .risk-medium { background: #ffa502; }
        .risk-high { background: #ff4757; }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 4px solid rgba(255,215,0,0.3);
            border-top-color: #FFD700;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .signal-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            margin-top: 10px;
        }
        .signal-bull { background: #00d084; color: #000; }
        .signal-bear { background: #ff4757; color: #fff; }
        .signal-neutral { background: #ffa502; color: #000; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔶 铜价预测系统</h1>
            <p class="subtitle">增强版 - 四层宏观因子 + 风险量化</p>
        </header>

        <div class="price-card">
            <div class="price-label">当前铜价</div>
            <div class="price-value" id="currentPrice">--</div>
            <div style="color: #666; margin-top: 10px;">上海期货交易所 CU 主力合约</div>
            <br>
            <button class="btn" id="predictBtn" onclick="runPrediction()">
                🔮 开始增强预测
            </button>
        </div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p style="color: #888;">正在运行四层宏观因子分析...</p>
        </div>

        <div id="results" class="results">
            <!-- 预测结果对比 -->
            <div class="result-card">
                <div class="result-title">📊 预测结果对比</div>
                <div class="prediction-grid">
                    <div class="prediction-box">
                        <div class="box-label">基础预测</div>
                        <div class="box-value" id="baseForecast">--</div>
                        <div class="box-change" id="baseChange">--</div>
                    </div>
                    <div class="prediction-box">
                        <div class="box-label">宏观调整后</div>
                        <div class="box-value" id="macroForecast">--</div>
                        <div class="box-change" id="macroChange">--</div>
                    </div>
                    <div class="prediction-box highlight">
                        <div class="box-label">⭐ 最终预测区间</div>
                        <div class="box-value" id="finalForecast">--</div>
                        <div class="box-change" id="finalChange">--</div>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <div style="color: #888; margin-bottom: 10px;">宏观信号</div>
                    <span class="signal-badge" id="macroSignal">--</span>
                </div>
            </div>

            <!-- 风险量化 -->
            <div class="result-card">
                <div class="result-title">🛡️ 风险量化分析</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <div>
                        <div style="color: #888; margin-bottom: 10px;">不确定性</div>
                        <div style="font-size: 32px; font-weight: bold;" id="uncertainty">--</div>
                        <div class="risk-bar">
                            <div class="risk-fill" id="uncertaintyBar"></div>
                        </div>
                    </div>
                    <div>
                        <div style="color: #888; margin-bottom: 10px;">95% 预测区间</div>
                        <div style="font-size: 18px;" id="predictionRange">--</div>
                    </div>
                    <div>
                        <div style="color: #888; margin-bottom: 10px;">宏观调整幅度</div>
                        <div style="font-size: 32px; font-weight: bold;" id="macroAdjustment">--</div>
                    </div>
                </div>
            </div>

            <!-- 宏观因子 -->
            <div class="result-card">
                <div class="result-title">🌍 四层宏观因子</div>
                <div class="macro-section" id="macroSection">
                    <!-- 动态填充 -->
                </div>
            </div>

            <div style="text-align: center; color: #666; margin-top: 20px;">
                <p>预测时间: <span id="predictTime">--</span></p>
                <p style="margin-top: 5px; font-size: 12px;">⚠️ 本预测仅供参考，不构成投资建议</p>
            </div>
        </div>
    </div>

    <script>
        async function runPrediction() {
            const btn = document.getElementById('predictBtn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            btn.disabled = true;
            loading.style.display = 'block';
            results.style.display = 'none';
            
            try {
                const response = await fetch('/api/predict');
                const data = await response.json();
                
                if (data.error) {
                    alert('预测失败: ' + data.error);
                    return;
                }
                
                const final = data.final_prediction;
                
                // 当前价格
                document.getElementById('currentPrice').textContent = 
                    '¥' + final.current_price.toLocaleString('zh-CN', {minimumFractionDigits: 2});
                
                // 基础预测
                document.getElementById('baseForecast').textContent = 
                    '¥' + final.base_forecast.toLocaleString('zh-CN', {minimumFractionDigits: 0});
                const baseChange = ((final.base_forecast - final.current_price) / final.current_price * 100);
                document.getElementById('baseChange').textContent = (baseChange >= 0 ? '+' : '') + baseChange.toFixed(2) + '%';
                document.getElementById('baseChange').className = 'box-change ' + (baseChange >= 0 ? 'up' : 'down');
                
                // 宏观调整后
                document.getElementById('macroForecast').textContent = 
                    '¥' + final.macro_adjusted_forecast.toLocaleString('zh-CN', {minimumFractionDigits: 0});
                const macroChange = ((final.macro_adjusted_forecast - final.current_price) / final.current_price * 100);
                document.getElementById('macroChange').textContent = (macroChange >= 0 ? '+' : '') + macroChange.toFixed(2) + '%';
                document.getElementById('macroChange').className = 'box-change ' + (macroChange >= 0 ? 'up' : 'down');
                
                // 最终预测
                document.getElementById('finalForecast').textContent = 
                    '¥' + final.final_forecast_range.point_estimate.toLocaleString('zh-CN', {minimumFractionDigits: 0});
                const finalChange = final.predicted_change.total_pct;
                document.getElementById('finalChange').textContent = (finalChange >= 0 ? '+' : '') + finalChange.toFixed(2) + '%';
                document.getElementById('finalChange').className = 'box-change ' + (finalChange >= 0 ? 'up' : 'down');
                
                // 宏观信号
                const signalEl = document.getElementById('macroSignal');
                signalEl.textContent = final.macro_signal;
                signalEl.className = 'signal-badge ' + (final.macro_signal.includes('看涨') ? 'signal-bull' : final.macro_signal.includes('看跌') ? 'signal-bear' : 'signal-neutral');
                
                // 风险量化
                document.getElementById('uncertainty').textContent = (final.uncertainty * 100).toFixed(1) + '%';
                const uncBar = document.getElementById('uncertaintyBar');
                uncBar.style.width = Math.min(final.uncertainty * 500, 100) + '%';
                uncBar.className = 'risk-fill ' + (final.uncertainty < 0.1 ? 'risk-low' : final.uncertainty < 0.15 ? 'risk-medium' : 'risk-high');
                
                document.getElementById('predictionRange').innerHTML = 
                    '[¥' + final.final_forecast_range.lower_95.toLocaleString('zh-CN', {minimumFractionDigits: 0}) + 
                    ' ~ ¥' + final.final_forecast_range.upper_95.toLocaleString('zh-CN', {minimumFractionDigits: 0}) + ']';
                
                document.getElementById('macroAdjustment').textContent = 
                    (final.predicted_change.macro_adjustment_pct >= 0 ? '+' : '') + 
                    final.predicted_change.macro_adjustment_pct.toFixed(2) + '%';
                document.getElementById('macroAdjustment').style.color = final.predicted_change.macro_adjustment_pct >= 0 ? '#00d084' : '#ff4757';
                
                // 宏观因子（简化显示）
                const macroSection = document.getElementById('macroSection');
                macroSection.innerHTML = `
                    <div class="macro-card">
                        <div class="macro-title">🇨🇳 中国实体经济</div>
                        <div class="macro-item"><span>官方PMI</span><span>49.8</span></div>
                        <div class="macro-item"><span>财新PMI</span><span>51.2</span></div>
                        <div class="macro-item"><span>M1-M2剪刀差</span><span>-3.2%</span></div>
                    </div>
                    <div class="macro-card">
                        <div class="macro-title">💵 美元与流动性</div>
                        <div class="macro-item"><span>美元指数</span><span>103.5</span></div>
                        <div class="macro-item"><span>实际利率(TIPS)</span><span>1.8%</span></div>
                        <div class="macro-item"><span>联邦基金利率</span><span>4.38%</span></div>
                    </div>
                    <div class="macro-card">
                        <div class="macro-title">🏭 全球工业周期</div>
                        <div class="macro-item"><span>全球制造业PMI</span><span>50.3</span></div>
                        <div class="macro-item"><span>美国ISM</span><span>50.3</span></div>
                        <div class="macro-item"><span>欧盟工业产出</span><span>-1.5%</span></div>
                    </div>
                    <div class="macro-card">
                        <div class="macro-title">⚒️ 供应与政策</div>
                        <div class="macro-item"><span>铜TC/RC</span><span>85$/吨</span></div>
                        <div class="macro-item"><span>罢工风险</span><span>4/10</span></div>
                        <div class="macro-item"><span>全球库存天数</span><span>4.5天</span></div>
                    </div>
                `;
                
                // 预测时间
                document.getElementById('predictTime').textContent = new Date(data.timestamp).toLocaleString('zh-CN');
                
                // 显示结果
                loading.style.display = 'none';
                results.style.display = 'block';
                results.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                alert('请求失败: ' + error.message);
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/predict')
def predict():
    result = run_enhanced_prediction()
    return jsonify(result)

if __name__ == '__main__':
    print("="*60)
    print("🔶 铜价预测增强版 Web 服务器")
    print("="*60)
    print("访问地址: http://127.0.0.1:7778")
    print("="*60)
    app.run(debug=False, host='0.0.0.0', port=7778)
