"""
黄金价格预测 - 快速版本（不含LSTM）
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from config import *
from data_loader import GoldDataLoader
from models import RandomForestModel, ARIMAModel, LinearRegressionModel
from visualization import (
    plot_price_history, plot_model_comparison,
    plot_technical_indicators, plot_future_forecast
)

print("=" * 60)
print("黄金价格预测模型 (快速版)")
print("=" * 60)

# 加载数据
print("\n[1/4] 正在加载数据...")
loader = GoldDataLoader(symbol=GOLD_SYMBOL, start_date=START_DATE, end_date=END_DATE)
df = loader.fetch_data()

# 添加技术指标
print("\n[2/4] 正在计算技术指标...")
df = loader.add_technical_indicators(df)
df = df.dropna()

print(f"数据条数: {len(df)}")
print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")

# 划分训练集和测试集
train_size = int(len(df) * TRAIN_TEST_SPLIT)
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:]

# 训练模型
print("\n[3/4] 正在训练模型...")
predictions = {}
metrics = {}

# Random Forest
rf_model = RandomForestModel(n_estimators=50, max_depth=10)
X_train_rf, y_train_rf = rf_model.prepare_data(train_df, LOOKBACK_WINDOW)
X_test_rf_full, y_test_rf_full = rf_model.prepare_data(df, LOOKBACK_WINDOW)
train_idx = len(X_train_rf)
X_test_rf = X_test_rf_full[train_idx:]
y_test_rf = y_test_rf_full[train_idx:]
rf_model.train(X_train_rf, y_train_rf)
rf_pred = rf_model.predict(X_test_rf)
predictions['Random Forest'] = rf_model.scaler.inverse_transform(rf_pred).flatten()
metrics['Random Forest'] = rf_model.evaluate(y_test_rf, rf_pred)
print(f"Random Forest - RMSE: {metrics['Random Forest']['RMSE']:.2f}, R²: {metrics['Random Forest']['R2']:.4f}")

# Linear Regression
lr_model = LinearRegressionModel()
X_train_lr, y_train_lr = lr_model.prepare_data(train_df, LOOKBACK_WINDOW)
X_test_lr_full, y_test_lr_full = lr_model.prepare_data(df, LOOKBACK_WINDOW)
X_test_lr = X_test_lr_full[train_idx:]
y_test_lr = y_test_lr_full[train_idx:]
lr_model.train(X_train_lr, y_train_lr)
lr_pred = lr_model.predict(X_test_lr)
predictions['Linear Regression'] = lr_model.scaler.inverse_transform(lr_pred).flatten()
metrics['Linear Regression'] = lr_model.evaluate(y_test_lr, lr_pred)
print(f"Linear Regression - RMSE: {metrics['Linear Regression']['RMSE']:.2f}, R²: {metrics['Linear Regression']['R2']:.4f}")

# ARIMA
arima_model = ARIMAModel(order=(5, 1, 0))
train_data, _ = arima_model.prepare_data(train_df)
test_data, _ = arima_model.prepare_data(df)
arima_model.train(train_data)
arima_pred = arima_model.predict(start=len(train_data), end=len(df)-1)
arima_actual = test_data[len(train_data):]
arima_rmse = np.sqrt(np.mean((arima_actual - arima_pred) ** 2))
arima_r2 = 1 - np.sum((arima_actual - arima_pred) ** 2) / np.sum((arima_actual - np.mean(arima_actual)) ** 2)
predictions['ARIMA'] = arima_pred
metrics['ARIMA'] = {'RMSE': arima_rmse, 'R2': arima_r2}
print(f"ARIMA - RMSE: {metrics['ARIMA']['RMSE']:.2f}, R²: {metrics['ARIMA']['R2']:.4f}")

# 未来预测
print("\n[4/4] 正在预测未来价格...")
last_date = df['Date'].iloc[-1]
future_dates = pd.date_range(start=last_date, periods=FORECAST_HORIZON+1, freq='D')[1:]

future_forecasts = {}
future_forecasts['Random Forest'] = rf_model.forecast_future(X_test_rf[-1], days=FORECAST_HORIZON)
future_forecasts['Linear Regression'] = lr_model.forecast_future(X_test_lr[-1], days=FORECAST_HORIZON)
future_forecasts['ARIMA'] = arima_model.forecast_future(days=FORECAST_HORIZON)

# 输出结果
print("\n" + "=" * 60)
print("未来7天黄金价格预测")
print("=" * 60)
forecast_df = pd.DataFrame({'日期': future_dates.strftime('%Y-%m-%d')})
for name, pred in future_forecasts.items():
    forecast_df[name] = [f"${p:.2f}" for p in pred]
all_forecasts = np.array(list(future_forecasts.values()))
ensemble_pred = np.mean(all_forecasts, axis=0)
forecast_df['集成预测'] = [f"${p:.2f}" for p in ensemble_pred]
print(forecast_df.to_string(index=False))

# 趋势分析
current_price = df['Close'].iloc[-1]
avg_forecast = ensemble_pred[-1]
change_pct = ((avg_forecast - current_price) / current_price) * 100
print(f"\n当前价格: ${current_price:.2f}")
print(f"7天后预测: ${avg_forecast:.2f} ({change_pct:+.2f}%)")

print("\n" + "=" * 60)
print("模型性能排名 (按R²)")
print("=" * 60)
sorted_models = sorted(metrics.items(), key=lambda x: x[1]['R2'], reverse=True)
for i, (name, metric) in enumerate(sorted_models, 1):
    print(f"{i}. {name}: R² = {metric['R2']:.4f}")

print("\n✅ 完成!")
