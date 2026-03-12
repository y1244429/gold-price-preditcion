#!/usr/bin/env python3
"""
黄金价格预测主程序 - Web 版本
基于 main.py 的命令行版本
"""
from flask import Flask, render_template_string, jsonify
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os

warnings.filterwarnings('ignore')

app = Flask(__name__)

# 导入主程序模块
from config import *
from data_loader import GoldDataLoader
from models import (
    LSTMModel, RandomForestModel, ARIMAModel, LinearRegressionModel,
    TENSORFLOW_AVAILABLE
)

def run_gold_prediction():
    """运行黄金预测主程序"""
    try:
        print("=" * 60)
        print("黄金价格预测模型 - Web 版本")
        print("=" * 60)
        
        # 1. 加载数据
        print("\n[1/6] 正在加载数据...")
        loader = GoldDataLoader(symbol=GOLD_SYMBOL, start_date=START_DATE, end_date=END_DATE)
        df = loader.fetch_data()
        
        # 2. 添加技术指标
        print("\n[2/6] 正在计算技术指标...")
        df = loader.add_technical_indicators(df)
        df = df.dropna()
        
        current_price = df['Close'].iloc[-1]
        
        # 3. 准备数据
        train_size = int(len(df) * TRAIN_TEST_SPLIT)
        train_df = df.iloc[:train_size]
        test_df = df.iloc[train_size:]
        
        # 初始化模型
        models = {
            'Random Forest': RandomForestModel(n_estimators=RF_N_ESTIMATORS, max_depth=RF_MAX_DEPTH),
            'Linear Regression': LinearRegressionModel()
        }
        
        if TENSORFLOW_AVAILABLE:
            models['LSTM'] = LSTMModel(lookback_window=LOOKBACK_WINDOW, units=LSTM_UNITS)
        
        # 4. 训练模型
        print("\n[4/6] 正在训练模型...")
        predictions = {}
        metrics = {}
        
        # Random Forest
        print("训练 Random Forest...")
        rf_model = models['Random Forest']
        X_train_rf, y_train_rf = rf_model.prepare_data(train_df, LOOKBACK_WINDOW)
        X_test_rf_full, y_test_rf_full = rf_model.prepare_data(df, LOOKBACK_WINDOW)
        train_idx = len(X_train_rf)
        X_test_rf = X_test_rf_full[train_idx:]
        y_test_rf = y_test_rf_full[train_idx:]
        rf_model.train(X_train_rf, y_train_rf)
        rf_pred = rf_model.predict(X_test_rf)
        predictions['Random Forest'] = rf_model.scaler.inverse_transform(rf_pred).flatten().tolist()
        metrics['Random Forest'] = rf_model.evaluate(y_test_rf, rf_pred)
        
        # Linear Regression
        print("训练 Linear Regression...")
        lr_model = models['Linear Regression']
        X_train_lr, y_train_lr = lr_model.prepare_data(train_df, LOOKBACK_WINDOW)
        X_test_lr_full, y_test_lr_full = lr_model.prepare_data(df, LOOKBACK_WINDOW)
        X_test_lr = X_test_lr_full[train_idx:]
        y_test_lr = y_test_lr_full[train_idx:]
        lr_model.train(X_train_lr, y_train_lr)
        lr_pred = lr_model.predict(X_test_lr)
        predictions['Linear Regression'] = lr_model.scaler.inverse_transform(lr_pred).flatten().tolist()
        metrics['Linear Regression'] = lr_model.evaluate(y_test_lr, lr_pred)
        
        # ARIMA
        print("训练 ARIMA...")
        arima_model = ARIMAModel(order=ARIMA_ORDER)
        train_data, _ = arima_model.prepare_data(train_df)
        test_data, _ = arima_model.prepare_data(df)
        arima_model.train(train_data)
        arima_pred = arima_model.predict(start=len(train_data), end=len(df)-1)
        arima_actual = test_data[len(train_data):]
        arima_rmse = np.sqrt(np.mean((arima_actual - arima_pred) ** 2))
        arima_mae = np.mean(np.abs(arima_actual - arima_pred))
        arima_r2 = 1 - np.sum((arima_actual - arima_pred) ** 2) / np.sum((arima_actual - np.mean(arima_actual)) ** 2)
        arima_mape = np.mean(np.abs((arima_actual - arima_pred) / arima_actual)) * 100
        predictions['ARIMA'] = arima_pred.tolist()
        metrics['ARIMA'] = {'RMSE': arima_rmse, 'MAE': arima_mae, 'R2': arima_r2, 'MAPE': arima_mape}
        
        # 5. 未来预测
        print("\n[5/6] 正在生成未来预测...")
        last_date = df['Date'].iloc[-1]
        future_dates = pd.date_range(start=last_date, periods=FORECAST_HORIZON+1, freq='D')[1:]
        
        future_forecasts = {}
        future_forecasts['Random Forest'] = rf_model.forecast_future(X_test_rf[-1], days=FORECAST_HORIZON).tolist()
        future_forecasts['Linear Regression'] = lr_model.forecast_future(X_test_lr[-1], days=FORECAST_HORIZON).tolist()
        future_forecasts['ARIMA'] = arima_model.forecast_future(days=FORECAST_HORIZON).tolist()
        
        # 集成预测
        ensemble_forecast = []
        for i in range(FORECAST_HORIZON):
            avg = np.mean([future_forecasts[m][i] for m in future_forecasts])
            ensemble_forecast.append(float(avg))
        
        # 准备图表数据
        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': df['Close'].tolist(),
            'ma20': df['MA20'].tolist() if 'MA20' in df.columns else [],
            'ma60': df['MA60'].tolist() if 'MA60' in df.columns else [],
            'volume': df['Volume'].tolist(),
            'rsi': df['RSI'].tolist() if 'RSI' in df.columns else [],
            'macd': df['MACD'].tolist() if 'MACD' in df.columns else [],
            'bb_upper': df['BB_Upper'].tolist() if 'BB_Upper' in df.columns else [],
            'bb_lower': df['BB_Lower'].tolist() if 'BB_Lower' in df.columns else [],
        }
        
        # 转换 metrics 为可序列化
        for key in metrics:
            for k, v in metrics[key].items():
                if isinstance(v, (np.integer, np.floating)):
                    metrics[key][k] = float(v)
        
        return {
            'current_price': float(current_price),
            'timestamp': datetime.now().isoformat(),
            'data_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d'),
                'count': len(df)
            },
            'metrics': metrics,
            'future_dates': future_dates.strftime('%Y-%m-%d').tolist(),
            'future_forecasts': future_forecasts,
            'ensemble_forecast': ensemble_forecast,
            'chart_data': chart_data
        }
        
    except Exception as e:
        return {'error': str(e)}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🪙 黄金价格预测 - 主程序版</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,215,0,0.3);
            margin-bottom: 30px;
        }
        h1 {
            font-size: 36px;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 14px; }
        
        .price-card {
            background: linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,165,0,0.05));
            border: 2px solid rgba(255,215,0,0.4);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
        }
        .price-label { color: #aaa; font-size: 16px; text-transform: uppercase; letter-spacing: 2px; }
        .price-value {
            font-size: 64px;
            font-weight: bold;
            color: #FFD700;
            margin: 15px 0;
            text-shadow: 0 0 30px rgba(255,215,0,0.3);
        }
        
        .btn {
            background: linear-gradient(135deg, #FFD700, #FFA500);
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
        .result-title { color: #FFD700; font-size: 20px; margin-bottom: 20px; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
        }
        .metric-card h3 {
            color: #FFD700;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,215,0,0.3);
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .metric-row:last-child { border-bottom: none; }
        .metric-label { color: #888; }
        .metric-value { font-weight: bold; }
        .best-metric { color: #00d084; }
        
        .forecast-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .forecast-table th, .forecast-table td {
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .forecast-table th {
            background: rgba(255,215,0,0.1);
            color: #FFD700;
            font-weight: 600;
        }
        .forecast-table tr:hover { background: rgba(255,255,255,0.03); }
        .highlight { color: #FFD700; font-weight: bold; }
        
        .chart-container {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .chart-title { color: #FFD700; font-size: 18px; margin-bottom: 20px; }
        
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
        
        .data-info {
            text-align: center;
            color: #666;
            margin-top: 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🪙 黄金价格预测系统</h1>
            <p class="subtitle">主程序版 - Random Forest + Linear Regression + ARIMA</p>
        </header>

        <div class="price-card">
            <div class="price-label">当前黄金价格</div>
            <div class="price-value" id="currentPrice">--</div>
            <div class="data-info" id="dataInfo">--</div>
            <br>
            <button class="btn" id="predictBtn" onclick="runPrediction()">
                🔮 开始预测
            </button>
        </div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p style="color: #888;">正在训练模型并生成预测...</p>
        </div>

        <div id="results" class="results">
            <!-- 模型评估指标 -->
            <div class="result-card">
                <div class="result-title">📊 模型评估指标</div>
                <div class="metrics-grid" id="metricsGrid"></div>
            </div>

            <!-- 未来预测表格 -->
            <div class="result-card">
                <div class="result-title">🔮 未来7天价格预测</div>
                <table class="forecast-table">
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>Random Forest</th>
                            <th>Linear Regression</th>
                            <th>ARIMA</th>
                            <th class="highlight">集成预测</th>
                        </tr>
                    </thead>
                    <tbody id="forecastBody"></tbody>
                </table>
            </div>

            <!-- 价格走势图 -->
            <div class="chart-container">
                <div class="chart-title">📈 历史价格走势</div>
                <canvas id="priceChart" height="100"></canvas>
            </div>

            <!-- 预测对比图 -->
            <div class="chart-container">
                <div class="chart-title">📊 模型预测对比</div>
                <canvas id="forecastChart" height="100"></canvas>
            </div>

            <div style="text-align: center; color: #666; margin-top: 20px;">
                <p>预测时间: <span id="predictTime">--</span></p>
                <p style="margin-top: 5px; font-size: 12px;">⚠️ 本预测仅供参考，不构成投资建议</p>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
        let forecastChart = null;

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
                
                // 显示当前价格
                document.getElementById('currentPrice').textContent = 
                    '$' + data.current_price.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('dataInfo').textContent = 
                    `数据范围: ${data.data_range.start} 至 ${data.data_range.end} (${data.data_range.count} 条)`;
                
                // 模型评估指标
                const metricsGrid = document.getElementById('metricsGrid');
                metricsGrid.innerHTML = '';
                
                for (const [modelName, metric] of Object.entries(data.metrics)) {
                    const isBest = modelName === 'Linear Regression'; // 根据R²判断
                    const card = document.createElement('div');
                    card.className = 'metric-card';
                    card.innerHTML = `
                        <h3>${modelName}</h3>
                        <div class="metric-row">
                            <span class="metric-label">RMSE</span>
                            <span class="metric-value">${metric.RMSE?.toFixed(2) || '--'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">MAE</span>
                            <span class="metric-value">${metric.MAE?.toFixed(2) || '--'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">R²</span>
                            <span class="metric-value ${metric.R2 > 0.8 ? 'best-metric' : ''}">${metric.R2?.toFixed(4) || '--'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">MAPE</span>
                            <span class="metric-value">${metric.MAPE?.toFixed(2) || '--'}%</span>
                        </div>
                    `;
                    metricsGrid.appendChild(card);
                }
                
                // 预测表格
                const tbody = document.getElementById('forecastBody');
                tbody.innerHTML = '';
                
                for (let i = 0; i < data.future_dates.length; i++) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${data.future_dates[i]}</td>
                        <td>$${data.future_forecasts['Random Forest'][i].toFixed(2)}</td>
                        <td>$${data.future_forecasts['Linear Regression'][i].toFixed(2)}</td>
                        <td>$${data.future_forecasts['ARIMA'][i].toFixed(2)}</td>
                        <td class="highlight">$${data.ensemble_forecast[i].toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                }
                
                // 绘制图表
                drawPriceChart(data.chart_data);
                drawForecastChart(data.future_dates, data.future_forecasts, data.ensemble_forecast);
                
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

        function drawPriceChart(chartData) {
            const ctx = document.getElementById('priceChart').getContext('2d');
            
            if (priceChart) {
                priceChart.destroy();
            }
            
            priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.dates.slice(-90), // 最近90天
                    datasets: [{
                        label: '黄金价格',
                        data: chartData.prices.slice(-90),
                        borderColor: '#FFD700',
                        backgroundColor: 'rgba(255,215,0,0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }, {
                        label: 'MA20',
                        data: chartData.ma20.slice(-90),
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        pointRadius: 0,
                        tension: 0.4
                    }, {
                        label: 'MA60',
                        data: chartData.ma60.slice(-90),
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        pointRadius: 0,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { labels: { color: '#aaa' } }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888' } },
                        y: { 
                            grid: { color: 'rgba(255,255,255,0.1)' }, 
                            ticks: { color: '#888', callback: function(value) { return '$' + value; } }
                        }
                    }
                }
            });
        }

        function drawForecastChart(dates, forecasts, ensemble) {
            const ctx = document.getElementById('forecastChart').getContext('2d');
            
            if (forecastChart) {
                forecastChart.destroy();
            }
            
            forecastChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Random Forest',
                        data: forecasts['Random Forest'],
                        borderColor: '#22c55e',
                        borderWidth: 2,
                        pointRadius: 4,
                        tension: 0.4
                    }, {
                        label: 'Linear Regression',
                        data: forecasts['Linear Regression'],
                        borderColor: '#3b82f6',
                        borderWidth: 2,
                        pointRadius: 4,
                        tension: 0.4
                    }, {
                        label: 'ARIMA',
                        data: forecasts['ARIMA'],
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        pointRadius: 4,
                        tension: 0.4
                    }, {
                        label: '集成预测',
                        data: ensemble,
                        borderColor: '#FFD700',
                        backgroundColor: 'rgba(255,215,0,0.1)',
                        borderWidth: 3,
                        pointRadius: 5,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { labels: { color: '#aaa' } }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888' } },
                        y: { 
                            grid: { color: 'rgba(255,255,255,0.1)' }, 
                            ticks: { color: '#888', callback: function(value) { return '$' + value; } }
                        }
                    }
                }
            });
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
    result = run_gold_prediction()
    return jsonify(result)

if __name__ == '__main__':
    print("="*60)
    print("🪙 黄金价格预测主程序 - Web 服务器")
    print("="*60)
    print("访问地址: http://127.0.0.1:5556")
    print("="*60)
    app.run(debug=False, host='0.0.0.0', port=5556)
