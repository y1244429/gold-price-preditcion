"""
黄金价格预测 - 简化Web版本
使用模拟数据，无需额外依赖（仅需Flask）
"""
from flask import Flask, render_template, jsonify
import random
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# 生成模拟数据
def generate_mock_data():
    dates = []
    prices = []
    base_price = 1800
    
    start_date = datetime(2024, 1, 1)
    for i in range(365):
        date = start_date + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
        
        # 模拟价格波动
        change = random.uniform(-20, 25)
        base_price += change
        prices.append(round(base_price, 2))
    
    return dates, prices

# 生成预测数据
def generate_forecasts(last_price):
    forecasts = {
        'Random Forest': [],
        'Linear Regression': [],
        'ARIMA': [],
        'LSTM': []
    }
    
    for model in forecasts.keys():
        price = last_price
        for _ in range(7):
            change = random.uniform(-15, 20)
            price += change
            forecasts[model].append(round(price, 2))
    
    return forecasts

# 全局数据
dates, prices = generate_mock_data()
current_price = prices[-1]
forecasts = generate_forecasts(current_price)
future_dates = [(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]

@app.route('/')
def index():
    return render_template('simple_index.html')

@app.route('/api/data')
def get_data():
    # 计算移动平均线
    ma20 = []
    ma60 = []
    
    for i in range(len(prices)):
        if i >= 19:
            ma20.append(round(sum(prices[i-19:i+1]) / 20, 2))
        else:
            ma20.append(None)
        
        if i >= 59:
            ma60.append(round(sum(prices[i-59:i+1]) / 60, 2))
        else:
            ma60.append(None)
    
    # 计算RSI
    rsi = []
    for i in range(len(prices)):
        if i >= 14:
            gains = []
            losses = []
            for j in range(i-13, i+1):
                change = prices[j] - prices[j-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(round(100 - (100 / (1 + rs)), 2))
        else:
            rsi.append(50)
    
    return jsonify({
        'dates': dates[-90:],  # 最近90天
        'prices': prices[-90:],
        'ma20': ma20[-90:],
        'ma60': ma60[-90:],
        'rsi': rsi[-90:],
        'volume': [random.randint(100000, 500000) for _ in range(90)]
    })

@app.route('/api/current_price')
def get_current_price():
    prev_price = prices[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    return jsonify({
        'price': current_price,
        'change': round(change, 2),
        'change_pct': round(change_pct, 2),
        'date': dates[-1]
    })

@app.route('/api/metrics')
def get_metrics():
    return jsonify({
        'Random Forest': {'R2': 0.9234, 'RMSE': 12.45, 'MAE': 9.23, 'MAPE': 0.52},
        'Linear Regression': {'R2': 0.8912, 'RMSE': 15.67, 'MAE': 11.45, 'MAPE': 0.68},
        'ARIMA': {'R2': 0.8567, 'RMSE': 18.34, 'MAE': 13.21, 'MAPE': 0.81},
        'LSTM': {'R2': 0.9456, 'RMSE': 10.23, 'MAE': 7.89, 'MAPE': 0.43}
    })

@app.route('/api/forecasts')
def get_forecasts():
    return jsonify({
        'dates': future_dates,
        'predictions': forecasts
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("黄金价格预测系统 (简化版)")
    print("="*60)
    print(f"当前模拟价格: ${current_price}")
    print("\n启动Web服务器...")
    print("请访问: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
