"""
TensorFlow LSTM模型用于黄金价格预测
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 尝试导入TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
    print(f"✅ TensorFlow已加载，版本: {tf.__version__}")
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow未安装，LSTM模型将不可用")


def prepare_lstm_data(prices, lookback=20):
    """
    为LSTM准备数据
    LSTM需要3D输入: (samples, timesteps, features)
    """
    X, y = [], []
    for i in range(lookback, len(prices)):
        X.append(prices[i-lookback:i])
        y.append(prices[i])
    
    X = np.array(X)
    y = np.array(y)
    
    # 重塑为LSTM需要的3D格式: (samples, timesteps, features)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    return X, y


def build_lstm_model(lookback=20, use_simple=True):
    """
    构建LSTM模型
    
    Args:
        lookback: 回看天数
        use_simple: 是否使用简化模型（更快）
    """
    if not TF_AVAILABLE:
        return None
    
    if use_simple:
        # 简化模型：1层LSTM，更快
        model = Sequential([
            LSTM(32, input_shape=(lookback, 1)),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
    else:
        # 完整模型：3层LSTM，更精确但更慢
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
    
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
    
    return model


def normalize_data(data, min_val=None, max_val=None):
    """Min-Max归一化到0-1范围"""
    if min_val is None:
        min_val = np.min(data)
    if max_val is None:
        max_val = np.max(data)
    range_val = max_val - min_val
    if range_val == 0:
        range_val = 1
    normalized = (data - min_val) / range_val
    return normalized, min_val, max_val

def denormalize_data(normalized_data, min_val, max_val):
    """反归一化回原始范围"""
    return normalized_data * (max_val - min_val) + min_val

def train_lstm(prices, lookback=20, epochs=15, batch_size=32, use_simple=True):
    """
    训练LSTM模型 - 带数据归一化
    
    Args:
        prices: 价格数据
        lookback: 回看天数
        epochs: 训练轮数
        batch_size: 批次大小
        use_simple: 是否使用简化模型
    
    Returns:
        dict: 包含模型、预测结果、评估指标
    """
    if not TF_AVAILABLE:
        return {
            'status': 'error',
            'message': 'TensorFlow未安装',
            'predictions': [],
            'metrics': {}
        }
    
    try:
        print(f"🧠 准备LSTM数据...")
        
        # 数据归一化
        prices_normalized, price_min, price_max = normalize_data(prices)
        print(f"   数据归一化: 原始范围 [{price_min:.2f}, {price_max:.2f}] -> [0, 1]")
        
        X, y = prepare_lstm_data(prices_normalized, lookback)
        
        # 划分训练测试集
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        print(f"   训练集: {len(X_train)} 样本")
        print(f"   测试集: {len(X_test)} 样本")
        
        # 构建模型
        model_type = "简化" if use_simple else "完整"
        print(f"🧠 构建{model_type}LSTM模型...")
        model = build_lstm_model(lookback, use_simple=use_simple)
        if model is None:
            raise Exception("模型构建失败")
        
        # 训练 - 使用early stopping减少不必要训练
        print(f"🧠 训练LSTM模型 (epochs={epochs})...")
        
        # 设置TensorFlow日志级别，减少输出
        import os
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        tf.get_logger().setLevel('ERROR')
        
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            verbose=0  # 静默训练
        )
        
        # 预测
        print("🧠 LSTM预测中...")
        lstm_pred_normalized = model.predict(X_test, verbose=0).flatten()
        
        # 反归一化预测结果
        lstm_pred = denormalize_data(lstm_pred_normalized, price_min, price_max)
        y_test_denorm = denormalize_data(y_test, price_min, price_max)
        
        # 计算指标（使用反归一化后的数据）
        mse = np.mean((y_test_denorm - lstm_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_test_denorm - lstm_pred))
        mape = np.mean(np.abs((y_test_denorm - lstm_pred) / y_test_denorm)) * 100
        
        # R2
        ss_res = np.sum((y_test_denorm - lstm_pred) ** 2)
        ss_tot = np.sum((y_test_denorm - np.mean(y_test_denorm)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        metrics = {
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape,
            'R2': r2
        }
        
        print(f"✅ LSTM训练完成，R²={r2:.4f}, RMSE={rmse:.2f}")
        
        # 未来7天预测
        print("🧠 LSTM预测未来7天...")
        future_predictions = []
        # 使用归一化的最新数据
        current_seq = prices_normalized[-lookback:].copy()
        
        for _ in range(7):
            # 准备输入
            X_pred = current_seq.reshape(1, lookback, 1)
            pred_normalized = model.predict(X_pred, verbose=0)[0][0]
            
            # 反归一化预测值
            pred = denormalize_data(pred_normalized, price_min, price_max)
            future_predictions.append(float(pred))
            
            # 更新序列（使用归一化值）
            current_seq = np.roll(current_seq, -1)
            current_seq[-1] = pred_normalized
        
        return {
            'status': 'success',
            'model': model,
            'predictions': lstm_pred.tolist(),
            'actual': y_test_denorm.tolist(),
            'metrics': metrics,
            'future': future_predictions,
            'history': history.history
        }
        
    except Exception as e:
        print(f"❌ LSTM训练失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e),
            'predictions': [],
            'metrics': {}
        }


def get_lstm_prediction(prices, lookback=20):
    """
    获取LSTM预测结果（简化接口）
    """
    result = train_lstm(prices, lookback)
    
    if result['status'] == 'success':
        return {
            'metrics': result['metrics'],
            'predictions': result['predictions'],
            'future': result['future'],
            'actual': result['actual']
        }
    else:
        return None


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("测试TensorFlow LSTM模型")
    print("=" * 70)
    
    if TF_AVAILABLE:
        # 生成测试数据
        np.random.seed(42)
        test_prices = np.cumsum(np.random.randn(200) * 10) + 700
        
        result = train_lstm(test_prices, epochs=30)
        
        if result['status'] == 'success':
            print("\n✅ LSTM测试成功!")
            print(f"未来7天预测: {result['future']}")
    else:
        print("❌ 请先安装TensorFlow: pip install tensorflow")
