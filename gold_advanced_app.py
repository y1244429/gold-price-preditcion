"""
黄金价格高级预测系统 - 三维度预测
1. 短期预测 (3-10天) - 技术指标 + 市场情绪
2. 中期预测 (10-30天) - 宏观数据 + 机器学习
3. 长期预测 (30-90天) - 基本面分析 + 趋势模型
"""
from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import requests
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# ============== 数据获取模块 ==============

def get_gold_data():
    """获取黄金数据"""
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="5y")
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return generate_mock_data()

def generate_mock_data():
    """生成模拟数据"""
    dates = pd.date_range(end=datetime.now(), periods=1500, freq='D')
    np.random.seed(42)
    base_price = 1800
    prices = []
    for i in range(1500):
        trend = np.sin(i / 100) * 100
        noise = np.random.randn() * 15
        seasonal = 50 * np.sin(2 * np.pi * i / 365)
        price = base_price + trend + noise + seasonal + i * 0.3
        prices.append(max(price, 1500))
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p + 10 for p in prices],
        'Low': [p - 10 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(100000, 500000, 1500)
    })

def get_macro_data():
    """获取宏观数据"""
    try:
        # 美元指数
        dxy = yf.Ticker("DX-Y.NYB").history(period="2y")
        # 实际利率（10年期国债）
        tnx = yf.Ticker("^TNX").history(period="2y")
        # 原油
        oil = yf.Ticker("CL=F").history(period="2y")
        # 标普500
        sp500 = yf.Ticker("^GSPC").history(period="2y")
        
        macro = pd.DataFrame({
            'Date': dxy.index,
            'DXY': dxy['Close'].values,
            'RealRate': tnx['Close'].values[:len(dxy)],
            'Oil': oil['Close'].values[:len(dxy)],
            'SP500': sp500['Close'].values[:len(dxy)]
        })
        return macro
    except:
        return None

# ============== 技术指标计算 ==============

def calculate_indicators(df):
    """计算技术指标"""
    # 移动平均线
    for period in [5, 10, 20, 60]:
        df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 布林带
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 波动率
    df['Volatility'] = df['Close'].rolling(window=20).std()
    
    return df.dropna()

# ============== 短期预测 (3-10天) ==============

def short_term_forecast(df, days=10):
    """短期预测 - 基于技术指标"""
    prices = df['Close'].values
    
    # 特征工程
    features = []
    targets = []
    lookback = 10
    
    for i in range(lookback, len(prices)-days):
        feat = [
            prices[i-lookback:i].mean(),  # 均价
            prices[i-lookback:i].std(),   # 波动
            df['RSI'].iloc[i],            # RSI
            df['MACD'].iloc[i],           # MACD
            (prices[i] - df['MA20'].iloc[i]) / df['MA20'].iloc[i],  # 偏离度
            df['Volume'].iloc[i] / df['Volume'].iloc[i-5:i].mean(),  # 成交量比
        ]
        features.append(feat)
        targets.append(prices[i+days])
    
    X, y = np.array(features), np.array(targets)
    
    # 训练模型
    model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    split = int(len(X) * 0.8)
    model.fit(X[:split], y[:split])
    
    # 预测
    last_features = [features[-1]]
    predictions = []
    current_price = prices[-1]
    
    for i in range(days):
        pred = model.predict(last_features)[0]
        predictions.append(pred)
        # 更新特征
        last_features[0][0] = (last_features[0][0] * lookback + pred) / (lookback + 1)
    
    # 计算置信度
    test_pred = model.predict(X[split:])
    r2 = r2_score(y[split:], test_pred)
    
    return predictions, {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y[split:], test_pred))}

# ============== 中期预测 (10-30天) ==============

def medium_term_forecast(df, macro_df, days=30):
    """中期预测 - 基于宏观数据"""
    prices = df['Close'].values[-len(macro_df):]
    
    # 合并宏观数据
    features = []
    for i in range(len(prices)):
        feat = [
            prices[max(0, i-5):i+1].mean(),
            macro_df['DXY'].iloc[i] if 'DXY' in macro_df.columns else 100,
            macro_df['RealRate'].iloc[i] if 'RealRate' in macro_df.columns else 2.5,
            macro_df['Oil'].iloc[i] if 'Oil' in macro_df.columns else 80,
            macro_df['SP500'].iloc[i] if 'SP500' in macro_df.columns else 4000,
        ]
        features.append(feat)
    
    X = np.array(features[:-days])
    y = np.array(prices[days:])
    
    # 训练随机森林
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    split = int(len(X) * 0.8)
    model.fit(X[:split], y[:split])
    
    # 预测
    predictions = []
    last_feat = features[-1].copy()
    
    for i in range(days):
        pred = model.predict([last_feat])[0]
        predictions.append(pred)
        last_feat[0] = pred  # 更新价格均值
    
    # 计算性能
    test_pred = model.predict(X[split:])
    r2 = r2_score(y[split:], test_pred)
    
    return predictions, {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y[split:], test_pred))}

# ============== 长期预测 (30-90天) ==============

def long_term_forecast(df, days=90):
    """长期预测 - 基于基本面趋势"""
    prices = df['Close'].values
    
    # 使用长期趋势模型
    # 特征：长期均线、季节性、趋势
    features = []
    targets = []
    
    for i in range(60, len(prices)-days):
        feat = [
            prices[i-60:i].mean(),  # 60日均线
            prices[i-20:i].mean(),  # 20日均线
            (prices[i] - prices[i-60]) / prices[i-60],  # 60日涨幅
            np.sin(2 * np.pi * i / 365),  # 季节性
            np.cos(2 * np.pi * i / 365),
        ]
        features.append(feat)
        targets.append(prices[i+days])
    
    X, y = np.array(features), np.array(targets)
    
    # 线性回归 + 趋势
    model = LinearRegression()
    split = int(len(X) * 0.8)
    model.fit(X[:split], y[:split])
    
    # 预测
    predictions = []
    last_feat = features[-1].copy()
    
    for i in range(days):
        pred = model.predict([last_feat])[0]
        predictions.append(pred)
        # 更新特征
        last_feat[0] = (last_feat[0] * 59 + pred) / 60
        last_feat[1] = (last_feat[1] * 19 + pred) / 20
    
    # 计算性能
    test_pred = model.predict(X[split:])
    r2 = r2_score(y[split:], test_pred)
    
    return predictions, {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y[split:], test_pred))}

# ============== Flask路由 ==============

@app.route('/')
def index():
    return render_template('gold_advanced.html')

@app.route('/api/predictions')
def get_predictions():
    """获取三维度预测"""
    # 获取数据
    df = get_gold_data()
    df = calculate_indicators(df)
    macro_df = get_macro_data()
    
    # 短期预测 (3-10天)
    short_pred, short_metrics = short_term_forecast(df, days=10)
    
    # 中期预测 (10-30天)
    if macro_df is not None and len(macro_df) > 100:
        medium_pred, medium_metrics = medium_term_forecast(df, macro_df, days=30)
    else:
        # 无宏观数据时使用技术指标
        medium_pred, medium_metrics = short_term_forecast(df, days=30)
    
    # 长期预测 (30-90天)
    long_pred, long_metrics = long_term_forecast(df, days=90)
    
    # 生成日期
    base_date = datetime.now()
    short_dates = [(base_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(10)]
    medium_dates = [(base_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(30)]
    long_dates = [(base_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(90)]
    
    return jsonify({
        'current_price': round(df['Close'].iloc[-1], 2),
        'short_term': {
            'dates': short_dates,
            'predictions': [round(p, 2) for p in short_pred],
            'metrics': {k: round(v, 4) for k, v in short_metrics.items()},
            'method': '技术指标 + 机器学习'
        },
        'medium_term': {
            'dates': medium_dates,
            'predictions': [round(p, 2) for p in medium_pred],
            'metrics': {k: round(v, 4) for k, v in medium_metrics.items()},
            'method': '宏观数据 + 随机森林' if macro_df is not None else '技术指标扩展'
        },
        'long_term': {
            'dates': long_dates,
            'predictions': [round(p, 2) for p in long_pred],
            'metrics': {k: round(v, 4) for k, v in long_metrics.items()},
            'method': '基本面趋势 + 季节性'
        },
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    print("=" * 60)
    print("黄金价格高级预测系统")
    print("=" * 60)
    print("预测维度:")
    print("  1. 短期 (3-10天)  - 技术指标")
    print("  2. 中期 (10-30天) - 宏观数据")
    print("  3. 长期 (30-90天) - 基本面")
    print("=" * 60)
    print("请访问: http://127.0.0.1:8080")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=8080)
