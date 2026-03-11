"""
黄金价格预测主程序
"""
import os
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
from visualization import (
    plot_price_history, plot_predictions, plot_model_comparison,
    plot_technical_indicators, plot_future_forecast
)


def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists('output'):
        os.makedirs('output')
    if not os.path.exists('output/plots'):
        os.makedirs('output/plots')


def main():
    """主程序"""
    print("=" * 60)
    print("黄金价格预测模型")
    print("=" * 60)
    
    # 确保输出目录存在
    ensure_output_dir()
    
    # 1. 加载数据
    print("\n[1/6] 正在加载数据...")
    loader = GoldDataLoader(symbol=GOLD_SYMBOL, start_date=START_DATE, end_date=END_DATE)
    df = loader.fetch_data()
    
    # 2. 添加技术指标
    print("\n[2/6] 正在计算技术指标...")
    df = loader.add_technical_indicators(df)
    df = df.dropna()
    
    print(f"数据时间范围: {df['Date'].min()} 至 {df['Date'].max()}")
    print(f"数据条数: {len(df)}")
    print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    
    # 绘制历史价格走势
    plot_price_history(df, save_path='output/plots/01_price_history.png')
    plot_technical_indicators(df, save_path='output/plots/02_technical_indicators.png')
    
    # 3. 准备数据
    print("\n[3/6] 正在准备训练数据...")
    
    # 划分训练集和测试集
    train_size = int(len(df) * TRAIN_TEST_SPLIT)
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    
    print(f"训练集大小: {len(train_df)}, 测试集大小: {len(test_df)}")
    
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
    
    # LSTM模型 (仅当TensorFlow可用时)
    train_idx = None
    if TENSORFLOW_AVAILABLE and 'LSTM' in models:
        print("\n训练 LSTM 模型...")
        lstm_model = models['LSTM']
        X_train, y_train = lstm_model.prepare_data(train_df, LOOKBACK_WINDOW)
        X_test_full, y_test_full = lstm_model.prepare_data(df, LOOKBACK_WINDOW)
        
        # 只使用训练数据训练
        train_idx = len(X_train)
        X_test = X_test_full[train_idx:]
        y_test = y_test_full[train_idx:]
        
        lstm_model.train(X_train, y_train, epochs=LSTM_EPOCHS, batch_size=LSTM_BATCH_SIZE)
        lstm_pred = lstm_model.predict(X_test)
        predictions['LSTM'] = lstm_model.scaler.inverse_transform(lstm_pred).flatten()
        metrics['LSTM'] = lstm_model.evaluate(y_test, lstm_pred)
        print(f"LSTM - RMSE: {metrics['LSTM']['RMSE']:.2f}, R²: {metrics['LSTM']['R2']:.4f}")
    
    # 随机森林模型
    print("\n训练 Random Forest 模型...")
    rf_model = models['Random Forest']
    X_train_rf, y_train_rf = rf_model.prepare_data(train_df, LOOKBACK_WINDOW)
    X_test_rf_full, y_test_rf_full = rf_model.prepare_data(df, LOOKBACK_WINDOW)
    
    train_idx_rf = len(X_train_rf)
    X_test_rf = X_test_rf_full[train_idx_rf:]
    y_test_rf = y_test_rf_full[train_idx_rf:]
    
    rf_model.train(X_train_rf, y_train_rf)
    rf_pred = rf_model.predict(X_test_rf)
    predictions['Random Forest'] = rf_model.scaler.inverse_transform(rf_pred).flatten()
    metrics['Random Forest'] = rf_model.evaluate(y_test_rf, rf_pred)
    print(f"Random Forest - RMSE: {metrics['Random Forest']['RMSE']:.2f}, R²: {metrics['Random Forest']['R2']:.4f}")
    
    # 线性回归模型
    print("\n训练 Linear Regression 模型...")
    lr_model = models['Linear Regression']
    X_train_lr, y_train_lr = lr_model.prepare_data(train_df, LOOKBACK_WINDOW)
    X_test_lr_full, y_test_lr_full = lr_model.prepare_data(df, LOOKBACK_WINDOW)
    
    train_idx_lr = len(X_train_lr)
    X_test_lr = X_test_lr_full[train_idx_lr:]
    y_test_lr = y_test_lr_full[train_idx_lr:]
    
    lr_model.train(X_train_lr, y_train_lr)
    lr_pred = lr_model.predict(X_test_lr)
    predictions['Linear Regression'] = lr_model.scaler.inverse_transform(lr_pred).flatten()
    metrics['Linear Regression'] = lr_model.evaluate(y_test_lr, lr_pred)
    print(f"Linear Regression - RMSE: {metrics['Linear Regression']['RMSE']:.2f}, R²: {metrics['Linear Regression']['R2']:.4f}")
    
    # ARIMA模型
    print("\n训练 ARIMA 模型...")
    arima_model = ARIMAModel(order=ARIMA_ORDER)
    train_data, _ = arima_model.prepare_data(train_df)
    test_data, _ = arima_model.prepare_data(df)
    
    arima_model.train(train_data)
    arima_pred = arima_model.predict(start=len(train_data), end=len(df)-1)
    
    # ARIMA评估
    arima_actual = test_data[len(train_data):]
    arima_rmse = np.sqrt(np.mean((arima_actual - arima_pred) ** 2))
    arima_mae = np.mean(np.abs(arima_actual - arima_pred))
    arima_r2 = 1 - np.sum((arima_actual - arima_pred) ** 2) / np.sum((arima_actual - np.mean(arima_actual)) ** 2)
    arima_mape = np.mean(np.abs((arima_actual - arima_pred) / arima_actual)) * 100
    
    predictions['ARIMA'] = arima_pred
    metrics['ARIMA'] = {
        'RMSE': arima_rmse,
        'MAE': arima_mae,
        'R2': arima_r2,
        'MAPE': arima_mape
    }
    print(f"ARIMA - RMSE: {metrics['ARIMA']['RMSE']:.2f}, R²: {metrics['ARIMA']['R2']:.4f}")
    
    # 5. 绘制结果
    print("\n[5/6] 正在生成可视化图表...")
    
    # 模型性能对比
    plot_model_comparison(metrics, save_path='output/plots/03_model_comparison.png')
    
    # 预测结果对比
    test_dates = df['Date'].iloc[-len(list(predictions.values())[0]):]
    
    # 6. 未来预测
    print("\n[6/6] 正在预测未来价格...")
    
    last_date = df['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date, periods=FORECAST_HORIZON+1, freq='D')[1:]
    
    future_forecasts = {}
    
    # LSTM未来预测
    if TENSORFLOW_AVAILABLE and 'LSTM' in models:
        last_sequence_lstm = X_test[-1]
        future_forecasts['LSTM'] = lstm_model.forecast_future(last_sequence_lstm, days=FORECAST_HORIZON)
    
    # 随机森林未来预测
    last_sequence_rf = X_test_rf[-1]
    future_forecasts['Random Forest'] = rf_model.forecast_future(last_sequence_rf, days=FORECAST_HORIZON)
    
    # 线性回归未来预测
    last_sequence_lr = X_test_lr[-1]
    future_forecasts['Linear Regression'] = lr_model.forecast_future(last_sequence_lr, days=FORECAST_HORIZON)
    
    # ARIMA未来预测
    future_forecasts['ARIMA'] = arima_model.forecast_future(days=FORECAST_HORIZON)
    
    # 绘制未来预测
    plot_future_forecast(df, future_forecasts, days=FORECAST_HORIZON, 
                         save_path='output/plots/04_future_forecast.png')
    
    # 7. 输出预测结果
    print("\n" + "=" * 60)
    print("未来7天黄金价格预测")
    print("=" * 60)
    
    forecast_df = pd.DataFrame({
        '日期': future_dates.strftime('%Y-%m-%d')
    })
    
    for name, pred in future_forecasts.items():
        forecast_df[name] = [f"${p:.2f}" for p in pred]
    
    # 计算集成预测（各模型平均）
    all_forecasts = np.array(list(future_forecasts.values()))
    ensemble_pred = np.mean(all_forecasts, axis=0)
    forecast_df['集成预测'] = [f"${p:.2f}" for p in ensemble_pred]
    
    print("\n", forecast_df.to_string(index=False))
    
    # 趋势分析
    current_price = df['Close'].iloc[-1]
    avg_forecast = ensemble_pred[-1]
    change_pct = ((avg_forecast - current_price) / current_price) * 100
    
    print("\n" + "=" * 60)
    print("趋势分析")
    print("=" * 60)
    print(f"当前价格: ${current_price:.2f}")
    print(f"7天后预测平均价格: ${avg_forecast:.2f}")
    print(f"预测变化: {change_pct:+.2f}%")
    
    if change_pct > 2:
        trend = "强烈看涨 📈"
    elif change_pct > 0.5:
        trend = "看涨 ↑"
    elif change_pct < -2:
        trend = "强烈看跌 📉"
    elif change_pct < -0.5:
        trend = "看跌 ↓"
    else:
        trend = "横盘震荡 →"
    
    print(f"预测趋势: {trend}")
    
    # 模型推荐
    print("\n" + "=" * 60)
    print("模型性能排名 (按R²)")
    print("=" * 60)
    sorted_models = sorted(metrics.items(), key=lambda x: x[1]['R2'], reverse=True)
    for i, (name, metric) in enumerate(sorted_models, 1):
        print(f"{i}. {name}: R² = {metric['R2']:.4f}, RMSE = ${metric['RMSE']:.2f}")
    
    # 保存结果
    print("\n正在保存结果...")
    df.to_csv('output/gold_data_with_indicators.csv', index=False)
    forecast_df.to_csv('output/price_forecast.csv', index=False)
    
    metrics_df = pd.DataFrame(metrics).T
    metrics_df.to_csv('output/model_metrics.csv')
    
    print("\n✅ 完成! 结果已保存到 output/ 目录")
    print("   - gold_data_with_indicators.csv: 带技术指标的数据")
    print("   - price_forecast.csv: 价格预测结果")
    print("   - model_metrics.csv: 模型性能指标")
    print("   - output/plots/: 可视化图表")


if __name__ == "__main__":
    main()
