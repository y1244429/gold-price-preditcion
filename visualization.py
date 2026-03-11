"""
黄金价格预测可视化模块
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")


def plot_price_history(df, save_path=None):
    """绘制历史价格走势"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 价格走势图
    ax1 = axes[0]
    ax1.plot(df['Date'], df['Close'], label='收盘价', linewidth=2, color='gold')
    if 'MA20' in df.columns:
        ax1.plot(df['Date'], df['MA20'], label='MA20', alpha=0.7, color='blue')
    if 'MA60' in df.columns:
        ax1.plot(df['Date'], df['MA60'], label='MA60', alpha=0.7, color='red')
    
    ax1.set_title('黄金价格历史走势', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('价格 (USD)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 成交量
    ax2 = axes[1]
    ax2.bar(df['Date'], df['Volume'], alpha=0.6, color='orange')
    ax2.set_title('成交量', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('成交量')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_predictions(df, predictions_dict, future_dates, future_predictions, save_path=None):
    """绘制预测结果对比图"""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # 绘制历史数据
    ax.plot(df['Date'], df['Close'], label='历史价格', linewidth=2, color='black')
    
    # 绘制各模型预测
    colors = ['blue', 'green', 'red', 'purple']
    for i, (name, pred) in enumerate(predictions_dict.items()):
        pred_dates = df['Date'].iloc[-len(pred):]
        ax.plot(pred_dates, pred, label=f'{name} 预测', 
                linewidth=1.5, alpha=0.8, color=colors[i % len(colors)])
    
    # 绘制未来预测
    if future_predictions:
        for i, (name, pred) in enumerate(future_predictions.items()):
            ax.plot(future_dates, pred, label=f'{name} 未来预测', 
                    linewidth=2, linestyle='--', color=colors[i % len(colors)])
    
    ax.set_title('黄金价格预测结果对比', fontsize=16, fontweight='bold')
    ax.set_xlabel('日期')
    ax.set_ylabel('价格 (USD)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_model_comparison(metrics_dict, save_path=None):
    """绘制模型性能对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    models = list(metrics_dict.keys())
    rmse_values = [metrics_dict[m]['RMSE'] for m in models]
    mae_values = [metrics_dict[m]['MAE'] for m in models]
    r2_values = [metrics_dict[m]['R2'] for m in models]
    mape_values = [metrics_dict[m]['MAPE'] for m in models]
    
    # RMSE对比
    axes[0, 0].bar(models, rmse_values, color='steelblue')
    axes[0, 0].set_title('RMSE (均方根误差)', fontweight='bold')
    axes[0, 0].set_ylabel('数值')
    for i, v in enumerate(rmse_values):
        axes[0, 0].text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    # MAE对比
    axes[0, 1].bar(models, mae_values, color='forestgreen')
    axes[0, 1].set_title('MAE (平均绝对误差)', fontweight='bold')
    axes[0, 1].set_ylabel('数值')
    for i, v in enumerate(mae_values):
        axes[0, 1].text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    # R²对比
    axes[1, 0].bar(models, r2_values, color='coral')
    axes[1, 0].set_title('R² (决定系数)', fontweight='bold')
    axes[1, 0].set_ylabel('数值')
    axes[1, 0].set_ylim(0, 1)
    for i, v in enumerate(r2_values):
        axes[1, 0].text(i, v, f'{v:.4f}', ha='center', va='bottom')
    
    # MAPE对比
    axes[1, 1].bar(models, mape_values, color='mediumpurple')
    axes[1, 1].set_title('MAPE (平均绝对百分比误差 %)', fontweight='bold')
    axes[1, 1].set_ylabel('数值')
    for i, v in enumerate(mape_values):
        axes[1, 1].text(i, v, f'{v:.2f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_technical_indicators(df, save_path=None):
    """绘制技术指标图"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # MACD
    ax1 = axes[0]
    ax1.plot(df['Date'], df['MACD'], label='MACD', color='blue')
    ax1.plot(df['Date'], df['MACD_Signal'], label='Signal', color='red')
    ax1.bar(df['Date'], df['MACD_Histogram'], label='Histogram', 
            color='gray', alpha=0.5)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title('MACD指标', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # RSI
    ax2 = axes[1]
    ax2.plot(df['Date'], df['RSI'], color='purple', linewidth=1.5)
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买线(70)')
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖线(30)')
    ax2.fill_between(df['Date'], 30, 70, alpha=0.1, color='gray')
    ax2.set_title('RSI指标', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 布林带
    ax3 = axes[2]
    ax3.plot(df['Date'], df['Close'], label='收盘价', color='gold', linewidth=2)
    ax3.plot(df['Date'], df['BB_Upper'], label='上轨', color='red', alpha=0.7)
    ax3.plot(df['Date'], df['BB_Middle'], label='中轨', color='blue', alpha=0.7)
    ax3.plot(df['Date'], df['BB_Lower'], label='下轨', color='green', alpha=0.7)
    ax3.fill_between(df['Date'], df['BB_Lower'], df['BB_Upper'], alpha=0.1, color='gray')
    ax3.set_title('布林带', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_future_forecast(df, forecasts, days=7, save_path=None):
    """绘制未来预测图"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # 最近的历史数据
    recent_data = df.tail(60)
    ax.plot(recent_data['Date'], recent_data['Close'], 
            label='历史价格', linewidth=2, color='black')
    
    # 未来日期
    last_date = df['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date, periods=days+1, freq='D')[1:]
    
    # 各模型预测
    colors = ['blue', 'green', 'red', 'purple']
    for i, (name, pred) in enumerate(forecasts.items()):
        ax.plot(future_dates, pred, label=f'{name} 预测', 
                linewidth=2, marker='o', markersize=4, color=colors[i % len(colors)])
    
    # 预测区间标注
    all_preds = np.array(list(forecasts.values()))
    mean_pred = np.mean(all_preds, axis=0)
    std_pred = np.std(all_preds, axis=0)
    
    ax.fill_between(future_dates, mean_pred - std_pred, mean_pred + std_pred, 
                    alpha=0.2, color='orange', label='预测区间(±1σ)')
    
    ax.set_title(f'黄金价格未来{days}天预测', fontsize=16, fontweight='bold')
    ax.set_xlabel('日期')
    ax.set_ylabel('价格 (USD)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_residuals(y_true, y_pred_dict, save_path=None):
    """绘制残差分析图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    for idx, (name, y_pred) in enumerate(y_pred_dict.items()):
        ax = axes[idx // 2, idx % 2]
        residuals = y_true - y_pred
        
        ax.scatter(y_pred, residuals, alpha=0.5)
        ax.axhline(y=0, color='red', linestyle='--')
        ax.set_title(f'{name} - 残差图', fontweight='bold')
        ax.set_xlabel('预测值')
        ax.set_ylabel('残差')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
