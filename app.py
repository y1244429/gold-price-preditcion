"""
黄金价格预测Web应用
"""
from flask import Flask, render_template, jsonify, request
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from config import *
from data_loader import GoldDataLoader
from models import (
    LSTMModel, RandomForestModel, ARIMAModel, LinearRegressionModel,
    TENSORFLOW_AVAILABLE
)

app = Flask(__name__)

# 全局变量存储数据和模型
data_cache = {}
models_cache = {}
metrics_cache = {}
forecasts_cache = {}


def initialize_models():
    """初始化模型和数据"""
    print("正在初始化模型和数据...")
    
    # 加载数据
    loader = GoldDataLoader(symbol=GOLD_SYMBOL, start_date=START_DATE, end_date=END_DATE)
    df = loader.fetch_data()
    df = loader.add_technical_indicators(df)
    df = df.dropna()
    
    # 划分训练集和测试集
    train_size = int(len(df) * TRAIN_TEST_SPLIT)
    train_df = df.iloc[:train_size]
    
    # 初始化模型
    models = {
        'Random Forest': RandomForestModel(n_estimators=50, max_depth=10),
        'Linear Regression': LinearRegressionModel(),
        'ARIMA': ARIMAModel(order=ARIMA_ORDER)
    }
    
    if TENSORFLOW_AVAILABLE:
        models['LSTM'] = LSTMModel(lookback_window=LOOKBACK_WINDOW, units=LSTM_UNITS)
    
    predictions = {}
    metrics = {}
    
    # 训练 Random Forest
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
    
    # 训练 Linear Regression
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
    
    # 训练 ARIMA
    print("训练 ARIMA...")
    arima_model = models['ARIMA']
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
    
    # 训练 LSTM (可选)
    if TENSORFLOW_AVAILABLE and 'LSTM' in models:
        print("训练 LSTM...")
        lstm_model = models['LSTM']
        X_train, y_train = lstm_model.prepare_data(train_df, LOOKBACK_WINDOW)
        X_test_full, y_test_full = lstm_model.prepare_data(df, LOOKBACK_WINDOW)
        X_test = X_test_full[train_idx:]
        y_test = y_test_full[train_idx:]
        lstm_model.train(X_train, y_train, epochs=20, batch_size=LSTM_BATCH_SIZE)
        lstm_pred = lstm_model.predict(X_test)
        predictions['LSTM'] = lstm_model.scaler.inverse_transform(lstm_pred).flatten().tolist()
        metrics['LSTM'] = lstm_model.evaluate(y_test, lstm_pred)
    
    # 未来预测
    last_date = df['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date, periods=FORECAST_HORIZON+1, freq='D')[1:]
    
    future_forecasts = {}
    future_forecasts['Random Forest'] = rf_model.forecast_future(X_test_rf[-1], days=FORECAST_HORIZON).tolist()
    future_forecasts['Linear Regression'] = lr_model.forecast_future(X_test_lr[-1], days=FORECAST_HORIZON).tolist()
    future_forecasts['ARIMA'] = arima_model.forecast_future(days=FORECAST_HORIZON).tolist()
    
    if TENSORFLOW_AVAILABLE and 'LSTM' in models:
        future_forecasts['LSTM'] = lstm_model.forecast_future(X_test[-1], days=FORECAST_HORIZON).tolist()
    
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
    
    # 存储到缓存
    data_cache['df'] = df
    data_cache['chart_data'] = chart_data
    data_cache['future_dates'] = future_dates.strftime('%Y-%m-%d').tolist()
    models_cache['models'] = models
    models_cache['predictions'] = predictions
    metrics_cache['metrics'] = metrics
    forecasts_cache['forecasts'] = future_forecasts
    
    print("模型初始化完成!")


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """获取价格数据"""
    return jsonify(data_cache.get('chart_data', {}))


@app.route('/api/metrics')
def get_metrics():
    """获取模型指标"""
    return jsonify(metrics_cache.get('metrics', {}))


@app.route('/api/forecasts')
def get_forecasts():
    """获取预测结果"""
    return jsonify({
        'dates': forecasts_cache.get('future_dates', []),
        'predictions': forecasts_cache.get('forecasts', {})
    })


@app.route('/api/predictions')
def get_predictions():
    """获取历史预测对比"""
    return jsonify({
        'predictions': models_cache.get('predictions', {})
    })


@app.route('/api/current_price')
def get_current_price():
    """获取当前价格"""
    if 'df' in data_cache:
        df = data_cache['df']
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100
        
        return jsonify({
            'price': round(current_price, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'date': df['Date'].iloc[-1].strftime('%Y-%m-%d')
        })
    return jsonify({'error': '数据未加载'})


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """刷新数据"""
    try:
        initialize_models()
        return jsonify({'status': 'success', 'message': '数据已刷新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    # 初始化模型
    initialize_models()
    
    # 启动Flask应用
    print("\n启动Web服务器...")
    print("请访问: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
