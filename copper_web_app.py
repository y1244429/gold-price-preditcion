#!/usr/bin/env python3
"""
铜价预测基础版 Web 应用
基于 copper_prediction.py
"""
from flask import Flask, render_template_string, jsonify
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# 导入基础版铜价预测
def get_copper_data():
    """获取铜期货数据"""
    try:
        import akshare as ak
        contracts = ['CU2604', 'CU2505', 'CU2506']
        
        for contract in contracts:
            try:
                df = ak.futures_zh_daily_sina(symbol=contract)
                if df is not None and not df.empty:
                    df['Date'] = pd.to_datetime(df['date'])
                    df.set_index('Date', inplace=True)
                    df['Close'] = df['close'].astype(float)
                    df['Open'] = df['open'].astype(float)
                    df['High'] = df['high'].astype(float)
                    df['Low'] = df['low'].astype(float)
                    df['Volume'] = df['volume'].astype(float)
                    return df, contract
            except:
                continue
        
        # 备用：COMEX铜
        import yfinance as yf
        copper = yf.Ticker("HG=F")
        df = copper.history(period="1y")
        return df, "HG=F"
    except Exception as e:
        return None, str(e)

def calculate_indicators(df):
    """计算技术指标"""
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
    
    return df

def run_prediction():
    """运行铜价预测"""
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    
    df, source = get_copper_data()
    if df is None:
        return {'error': '无法获取数据'}
    
    df = calculate_indicators(df)
    df = df.dropna()
    
    current_price = df['Close'].iloc[-1]
    
    # 准备特征
    features = ['Close', 'MA5', 'MA20', 'RSI', 'MACD', 'Volatility']
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    X = df[features]
    y = df['Target']
    
    train_size = len(X) - 30
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
    
    # 训练模型
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=50, random_state=42)
    }
    
    predictions = {}
    model_details = {}
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        
        future_preds = []
        last_row = X.iloc[-1:].copy()
        
        for i in range(7):
            pred = model.predict(last_row)[0]
            future_preds.append(float(pred))
            last_row['Close'] = pred
        
        predictions[name] = future_preds
        model_details[name] = {
            'final': future_preds[-1],
            'change_pct': (future_preds[-1] - current_price) / current_price * 100
        }
    
    # 集成预测
    ensemble_preds = []
    for i in range(7):
        avg = np.mean([predictions[m][i] for m in predictions])
        ensemble_preds.append(float(avg))
    
    ensemble_change = (ensemble_preds[-1] - current_price) / current_price * 100
    
    # 生成日期
    dates = [(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]
    
    return {
        'current_price': float(current_price),
        'data_source': source,
        'timestamp': datetime.now().isoformat(),
        'models': model_details,
        'ensemble': {
            'predictions': ensemble_preds,
            'final': ensemble_preds[-1],
            'change_pct': ensemble_change
        },
        'daily_forecast': [
            {'date': dates[i], 'price': ensemble_preds[i], 
             'change_pct': (ensemble_preds[i] - current_price) / current_price * 100}
            for i in range(7)
        ]
    }

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔶 铜价预测 - 基础版</title>
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
        .container { max-width: 900px; margin: 0 auto; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,165,0,0.3);
            margin-bottom: 30px;
        }
        h1 {
            font-size: 32px;
            background: linear-gradient(135deg, #FFA500, #FF6347);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 14px; }
        
        .price-card {
            background: linear-gradient(135deg, rgba(255,165,0,0.15), rgba(255,99,71,0.05));
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
            color: #FFA500;
            margin: 15px 0;
            text-shadow: 0 0 30px rgba(255,165,0,0.3);
        }
        .price-change { font-size: 24px; margin-top: 10px; }
        .up { color: #00d084; }
        .down { color: #ff4757; }
        
        .btn {
            background: linear-gradient(135deg, #FFA500, #FF6347);
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
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(255,165,0,0.4); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .results { display: none; }
        .result-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .result-title { color: #FFA500; font-size: 18px; margin-bottom: 15px; }
        
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
            background: rgba(255,165,0,0.1);
            color: #FFA500;
            font-weight: 600;
        }
        .forecast-table tr:hover { background: rgba(255,255,255,0.03); }
        .highlight { color: #FFA500; font-weight: bold; }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 4px solid rgba(255,165,0,0.3);
            border-top-color: #FFA500;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .model-results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .model-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .model-name { color: #888; font-size: 14px; margin-bottom: 10px; }
        .model-price { font-size: 24px; font-weight: bold; color: #fff; }
        .model-change { font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔶 铜价预测系统</h1>
            <p class="subtitle">基础版 - 机器学习预测模型</p>
        </header>

        <div class="price-card">
            <div class="price-label">当前铜价</div>
            <div class="price-value" id="currentPrice">--</div>
            <div id="dataSource" style="color: #666; margin-top: 10px;">--</div>
            <br>
            <button class="btn" id="predictBtn" onclick="runPrediction()">
                🔮 开始预测
            </button>
        </div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p style="color: #888;">正在获取数据并训练模型...</p>
        </div>

        <div id="results" class="results">
            <div class="result-card">
                <div class="result-title">📊 模型预测结果</div>
                <div class="model-results" id="modelResults"></div>
            </div>

            <div class="result-card">
                <div class="result-title">📅 未来7天预测详情</div>
                <table class="forecast-table">
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>预测价格 (元/吨)</th>
                            <th>涨跌幅度</th>
                        </tr>
                    </thead>
                    <tbody id="forecastBody"></tbody>
                </table>
            </div>

            <div style="text-align: center; color: #666; margin-top: 20px;">
                <p>预测时间: <span id="predictTime">--</span></p>
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
                
                // 显示当前价格
                document.getElementById('currentPrice').textContent = 
                    '¥' + data.current_price.toLocaleString('zh-CN', {minimumFractionDigits: 2});
                document.getElementById('dataSource').textContent = '数据源: ' + data.data_source;
                
                // 模型结果
                const modelResults = document.getElementById('modelResults');
                modelResults.innerHTML = '';
                
                for (const [name, model] of Object.entries(data.models)) {
                    const changeClass = model.change_pct >= 0 ? 'up' : 'down';
                    const changeSymbol = model.change_pct >= 0 ? '+' : '';
                    
                    const card = document.createElement('div');
                    card.className = 'model-card';
                    card.innerHTML = `
                        <div class="model-name">${name}</div>
                        <div class="model-price">¥${model.final.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</div>
                        <div class="model-change ${changeClass}">${changeSymbol}${model.change_pct.toFixed(2)}%</div>
                    `;
                    modelResults.appendChild(card);
                }
                
                // 集成预测卡片
                const ensembleChangeClass = data.ensemble.change_pct >= 0 ? 'up' : 'down';
                const ensembleCard = document.createElement('div');
                ensembleCard.className = 'model-card';
                ensembleCard.style.border = '2px solid #FFA500';
                ensembleCard.innerHTML = `
                    <div class="model-name" style="color: #FFA500;">⭐ 集成预测</div>
                    <div class="model-price" style="color: #FFA500;">¥${data.ensemble.final.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</div>
                    <div class="model-change ${ensembleChangeClass}">${data.ensemble.change_pct >= 0 ? '+' : ''}${data.ensemble.change_pct.toFixed(2)}%</div>
                `;
                modelResults.appendChild(ensembleCard);
                
                // 每日预测表格
                const tbody = document.getElementById('forecastBody');
                tbody.innerHTML = '';
                
                data.daily_forecast.forEach(day => {
                    const changeClass = day.change_pct >= 0 ? 'up' : 'down';
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${day.date}</td>
                        <td class="highlight">¥${day.price.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
                        <td class="${changeClass}">${day.change_pct >= 0 ? '+' : ''}${day.change_pct.toFixed(2)}%</td>
                    `;
                    tbody.appendChild(row);
                });
                
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
    result = run_prediction()
    return jsonify(result)

if __name__ == '__main__':
    print("="*60)
    print("🔶 铜价预测基础版 Web 服务器")
    print("="*60)
    print("访问地址: http://127.0.0.1:7777")
    print("="*60)
    app.run(debug=False, host='0.0.0.0', port=7777)
