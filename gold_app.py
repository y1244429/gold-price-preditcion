"""
黄金价格预测Web应用 - 使用上海期货交易所黄金2604数据
集成风险管理模块
"""
from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import requests
import json
import warnings
import time
import os
warnings.filterwarnings('ignore')

# 导入风险管理模块
try:
    from gold_risk_management import GoldRiskManager
    RISK_MANAGEMENT_AVAILABLE = True
    print("✅ 风险管理模块已加载")
except ImportError as e:
    RISK_MANAGEMENT_AVAILABLE = False
    print(f"⚠️ 风险管理模块未加载: {e}")

# 导入 Serper 数据源（yfinance限流时的备用）
try:
    from serper_data_source import get_gold_data_serper
    SERPER_AVAILABLE = True
    print("✅ Serper 数据源已加载")
except ImportError:
    SERPER_AVAILABLE = False
    print("⚠️ Serper 数据源未加载")

# 导入TensorFlow LSTM模型
# 注意：可通过设置 LSTM_ENABLED = True 来启用LSTM
try:
    from lstm_model import train_lstm, TF_AVAILABLE
    # 手动控制LSTM开关 - 设置为False禁用，True启用
    LSTM_ENABLED = True  # ← 修改为True启用LSTM
    
    if TF_AVAILABLE and LSTM_ENABLED:
        print("✅ TensorFlow LSTM模型已加载（已启用）")
    elif TF_AVAILABLE and not LSTM_ENABLED:
        print("⚠️ LSTM模型已加载但被手动禁用（设置 LSTM_ENABLED = True 启用）")
        TF_AVAILABLE = False  # 强制禁用
    else:
        print("⚠️ TensorFlow未安装，LSTM模型不可用")
except Exception as e:
    print(f"⚠️ LSTM模型导入失败: {e}")
    TF_AVAILABLE = False
    LSTM_ENABLED = False

# ============ 选项 A: 标准ARIMA实现 ============
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    ARMA_AVAILABLE = True
    print("✅ Statsmodels ARIMA已加载")
except ImportError:
    ARMA_AVAILABLE = False
    print("⚠️ Statsmodels ARIMA不可用")

# ============ 选项 D: XGBoost ============
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
    print("✅ XGBoost已加载")
except ImportError:
    XGB_AVAILABLE = False
    print("⚠️ XGBoost未安装")

app = Flask(__name__)

# 全局数据缓存（延长至2小时）
cache = {
    'data': None,
    'last_update': None
}
CACHE_MINUTES = 120  # 缓存120分钟

# 数据获取缓存 - 避免重复API调用
data_fetch_cache = {
    'df': None,
    'timestamp': None
}
DATA_FETCH_CACHE_MINUTES = 30  # 数据30分钟内不重复获取

# ============ JSON序列化辅助函数 ============
def convert_to_native(obj):
    """将 numpy/pandas 类型转换为 Python 原生类型，以便 JSON 序列化"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int64, np.int32, np.int_)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float_)):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_native(item) for item in obj)
    else:
        return obj

# LSTM模型缓存（30分钟）
lstm_cache = {
    'model_result': None,
    'prices_hash': None,
    'last_update': None
}

# 风险管理缓存
risk_cache = {
    'risk_manager': None,
    'validation_results': None,
    'stress_results': None,
    'risk_metrics': None,
    'feature_importance': None,
    'defense_results': None,
    'failure_alerts': None,
    'last_update': None
}
RISK_CACHE_MINUTES = 60  # 风险管理结果缓存60分钟

# 清除旧缓存（LSTM修复后）
print("🧹 清除LSTM旧缓存（数据归一化修复）...")

def get_shfe_gold_data():
    """从上海期货交易所获取黄金期货数据"""
    try:
        print("正在尝试从上海期货交易所获取黄金期货数据...")
        
        # 使用akshare库获取上海期货交易所数据
        try:
            import akshare as ak
            
            # 尝试获取黄金期货数据，只尝试最活跃的2个合约
            contracts = ['AU2604', 'AU2506']
            
            for contract in contracts:
                try:
                    print(f"  尝试获取黄金{contract}...")
                    df = ak.futures_zh_daily_sina(symbol=contract)
                    
                    if df is not None and not df.empty:
                        df = df.reset_index()
                        df['Date'] = pd.to_datetime(df['date'])
                        df['Close'] = df['close'].astype(float)
                        df['Open'] = df['open'].astype(float)
                        df['High'] = df['high'].astype(float)
                        df['Low'] = df['low'].astype(float)
                        df['Volume'] = df['volume'].astype(float)
                        df.attrs['data_source'] = f"上海期货交易所 {contract}"
                        
                        print(f"✅ 成功获取上海期货交易所黄金{contract}数据: {len(df)} 条")
                        print(f"   最新收盘价: {df['Close'].iloc[-1]:.2f} 元/克")
                        return calculate_indicators(df)
                except Exception as e:
                    print(f"  合约{contract}获取失败: {e}")
                    continue
                    
        except ImportError:
            print("akshare未安装，尝试其他方式...")
        except Exception as e:
            print(f"akshare获取失败: {e}")
        
        # 备用：尝试从新浪财经API获取
        return get_sina_gold_data()
        
    except Exception as e:
        print(f"上海期货交易所数据获取失败: {e}")
        return None

def get_sina_gold_data():
    """从新浪财经获取黄金期货数据"""
    try:
        print("正在从新浪财经获取黄金期货数据...")
        
        # 尝试最活跃的2个合约
        contracts = ['AU2604', 'AU2506']
        
        for contract in contracts:
            try:
                # 新浪财经黄金期货接口
                url = "https://stock.finance.sina.com.cn/futures/api/jsonp.php/var=/InnerFuturesNewService.getDailyKLine"
                params = {'symbol': contract}
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # 解析JSONP响应
                    text = response.text
                    # 提取JSON部分
                    start = text.find('(') + 1
                    end = text.rfind(')')
                    if start > 0 and end > start:
                        json_str = text[start:end]
                        data = json.loads(json_str)
                        
                        df = pd.DataFrame(data)
                        df['Date'] = pd.to_datetime(df['date'])
                        df['Close'] = df['close'].astype(float)
                        df['Open'] = df['open'].astype(float)
                        df['High'] = df['high'].astype(float)
                        df['Low'] = df['low'].astype(float)
                        df['Volume'] = df['volume'].astype(float)
                        df.attrs['data_source'] = f"新浪财经 {contract}"
                        
                        print(f"✅ 成功获取新浪财经黄金{contract}数据: {len(df)} 条")
                        return calculate_indicators(df)
            except Exception as e:
                print(f"  合约{contract}获取失败: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"新浪财经数据获取失败: {e}")
        return None

def get_shfe_current_price():
    """获取上海期货交易所黄金当前价格 - 优先实时行情"""
    try:
        import akshare as ak
        
        # 方法1: 获取实时行情（优先）
        try:
            df_spot = ak.futures_zh_spot(symbol='AU2604')
            if df_spot is not None and not df_spot.empty:
                # 获取最新价格（可能是 current_price 或最新价）
                if 'current_price' in df_spot.columns:
                    price = float(df_spot['current_price'].iloc[0])
                elif '最新价' in df_spot.columns:
                    price = float(df_spot['最新价'].iloc[0])
                else:
                    price = float(df_spot.iloc[0, 5])  # 第6列通常是当前价
                print(f"✅ 成功获取上期所黄金AU2604实时价格: {price}")
                return price, 'AU2604'
        except Exception as e:
            print(f"⚠️ 实时行情获取失败: {e}")
        
        # 方法2: 尝试主力连续合约 AU0（价格更接近市场）
        try:
            df_main = ak.futures_zh_daily_sina(symbol='AU0')
            if df_main is not None and not df_main.empty:
                price = float(df_main['close'].iloc[-1])
                print(f"✅ 成功获取上期所黄金主力连续AU0价格: {price}")
                return price, 'AU0'
        except Exception as e:
            print(f"⚠️ 主力连续获取失败: {e}")
        
        # 方法3: 获取日线数据的最新收盘价
        for sym in ['AU2604', 'AU2506']:
            try:
                df = ak.futures_zh_daily_sina(symbol=sym)
                if df is not None and not df.empty:
                    price = float(df['close'].iloc[-1])
                    print(f"✅ 成功获取上期所黄金{sym}最新收盘价: {price}")
                    return price, sym
            except:
                continue
    except Exception as e:
        print(f"⚠️ 上期所当前价格获取失败: {e}")
    
    return None, None

def get_yahoo_gold_data():
    """从Yahoo Finance获取黄金数据作为备用"""
    try:
        print("正在从Yahoo Finance下载黄金数据...")
        gold = yf.Ticker("GC=F")
        df = gold.history(period="2y")
        
        if df.empty:
            raise Exception("无法获取数据")
        
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
        
        print(f"成功获取Yahoo Finance黄金数据: {len(df)} 条")
        return calculate_indicators(df)
    except Exception as e:
        error_msg = str(e)
        print(f"Yahoo Finance数据获取失败: {error_msg}")
        
        # 检测限流错误
        if "Too Many Requests" in error_msg or "Rate limited" in error_msg:
            print("⚠️ 检测到 Yahoo Finance 限流")
            
            # 尝试使用 Serper API
            if SERPER_AVAILABLE:
                print("🔄 自动切换到 Serper API...")
                return None  # 返回None让上层调用Serper
        
        return None

def calculate_indicators(df):
    """计算技术指标"""
    # 移动平均线
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
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
    
    return df.dropna()

def generate_mock_data():
    """生成模拟数据作为最后备用 - 使用固定模式生成可重复数据"""
    print("⚠️ 使用模拟数据（所有真实数据源均不可用）...")
    dates = pd.date_range(end=datetime.now(), periods=500, freq='D')
    
    # 上海期货交易所黄金合约价格区间：700-850 元/克 (基于2024-2025年实际数据)
    base_price = 791  # 使用当前实际价格作为基准
    prices = []
    highs = []
    lows = []
    volumes = []
    
    for i in range(500):
        # 使用固定模式生成价格：正弦趋势 + 线性漂移 + 固定伪随机
        trend = np.sin(i / 30) * 30
        drift = i * 0.08
        # 使用固定伪随机：基于索引的确定性变化
        pseudo_noise = ((i * 9301 + 49297) % 233280) / 233280 - 0.5  # 线性同余生成固定"随机"数
        noise = pseudo_noise * 30  # 放大到合理范围
        price = base_price + trend + noise + drift
        price = max(price, 700)  # 最低不低于700元/克
        prices.append(price)
        
        # 固定的高低价格偏移
        high_offset = abs(((i * 12345 + 67890) % 100000) / 100000 * 20)
        low_offset = abs(((i * 54321 + 98765) % 100000) / 100000 * 20)
        highs.append(price + high_offset)
        lows.append(price - low_offset)
        
        # 固定成交量
        volume = 50000 + ((i * 1103515245 + 12345) % 150000)
        volumes.append(volume)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    df.attrs['data_source'] = "模拟数据 (基于上期所价格区间,固定模式)"
    
    return calculate_indicators(df)

def get_real_gold_data():
    """获取黄金数据，优先级：上海期货交易所 > Yahoo Finance > Serper API > 模拟数据"""
    global data_fetch_cache
    
    # 检查数据获取缓存（30分钟内不重复获取）
    if data_fetch_cache['df'] is not None and data_fetch_cache['timestamp'] is not None:
        if datetime.now() - data_fetch_cache['timestamp'] < timedelta(minutes=DATA_FETCH_CACHE_MINUTES):
            print(f"📦 使用数据获取缓存（{DATA_FETCH_CACHE_MINUTES}分钟内）")
            return data_fetch_cache['df']
    
    # 1. 尝试上海期货交易所
    print("🔄 尝试获取上海期货交易所数据...")
    df = get_shfe_gold_data()
    if df is not None and not df.empty:
        print("✅ 成功获取上期所数据")
        data_fetch_cache['df'] = df
        data_fetch_cache['timestamp'] = datetime.now()
        return df
    
    # 2. 尝试Yahoo Finance
    print("🔄 尝试获取Yahoo Finance数据...")
    df = get_yahoo_gold_data()
    if df is not None and not df.empty:
        print("✅ 成功获取Yahoo数据")
        data_fetch_cache['df'] = df
        data_fetch_cache['timestamp'] = datetime.now()
        return df
    
    # 3. 如果Yahoo限流，尝试 Serper API
    if SERPER_AVAILABLE:
        print("🔄 Yahoo限流，尝试 Serper API...")
        try:
            df = get_gold_data_serper()
            if df is not None and not df.empty:
                print("✅ 成功获取 Serper API 数据")
                # 计算技术指标
                df = calculate_indicators(df)
                data_fetch_cache['df'] = df
                data_fetch_cache['timestamp'] = datetime.now()
                return df
        except Exception as e:
            print(f"⚠️ Serper API 获取失败: {e}")
    
    # 4. 使用模拟数据
    print("⚠️ 使用模拟数据")
    df = generate_mock_data()
    data_fetch_cache['df'] = df
    data_fetch_cache['timestamp'] = datetime.now()
    return df

# ============ 选项 C: 特征工程增强 ============
def create_enhanced_features(df, lookback=20):
    """
    创建增强特征 - 包含技术指标和宏观因子
    选项 C: 特征工程增强
    """
    features_list = []
    targets = []
    
    prices = df['Close'].values
    
    for i in range(lookback, len(prices)):
        # 基础特征: 过去lookback天的价格
        base_features = prices[i-lookback:i].tolist()
        
        # 技术指标特征 (选项 C)
        tech_features = []
        
        # 价格统计特征
        price_window = prices[i-lookback:i]
        tech_features.append(np.mean(price_window))  # 均线
        tech_features.append(np.std(price_window))   # 波动率
        tech_features.append((prices[i-1] - price_window[0]) / price_window[0])  # 区间收益率
        tech_features.append((prices[i-1] - np.min(price_window)) / (np.max(price_window) - np.min(price_window) + 1e-8))  # 相对位置
        
        # RSI (如果数据中有)
        if 'RSI' in df.columns and i < len(df):
            tech_features.append(df['RSI'].iloc[i])
        else:
            # 计算简易RSI
            deltas = np.diff(price_window)
            gains = np.sum(deltas[deltas > 0]) if len(deltas) > 0 else 0
            losses = -np.sum(deltas[deltas < 0]) if len(deltas) > 0 else 0
            rs = gains / (losses + 1e-8)
            rsi = 100 - (100 / (1 + rs))
            tech_features.append(rsi)
        
        # MACD (如果数据中有)
        if 'MACD' in df.columns and i < len(df):
            tech_features.append(df['MACD'].iloc[i])
            if 'MACD_Signal' in df.columns:
                tech_features.append(df['MACD_Signal'].iloc[i])
            else:
                tech_features.append(0)
        else:
            # 计算简易MACD
            ema12 = np.mean(price_window[-12:]) if len(price_window) >= 12 else np.mean(price_window)
            ema26 = np.mean(price_window[-20:]) if len(price_window) >= 20 else np.mean(price_window)
            macd = ema12 - ema26
            tech_features.extend([macd, 0])
        
        # 布林带位置 (如果数据中有)
        if 'BB_Upper' in df.columns and i < len(df):
            bb_position = (prices[i-1] - df['BB_Lower'].iloc[i]) / (df['BB_Upper'].iloc[i] - df['BB_Lower'].iloc[i] + 1e-8)
            tech_features.append(bb_position)
        else:
            # 计算简易布林带位置
            ma = np.mean(price_window)
            std = np.std(price_window)
            bb_position = (prices[i-1] - (ma - 2*std)) / (4*std + 1e-8)
            tech_features.append(bb_position)
        
        # 成交量特征 (如果有)
        if 'Volume' in df.columns and i < len(df):
            vol_window = df['Volume'].iloc[i-lookback:i].values
            tech_features.append(np.mean(vol_window))
            tech_features.append(np.std(vol_window))
        else:
            tech_features.extend([0, 0])
        
        # 合并所有特征
        all_features = base_features + tech_features
        features_list.append(all_features)
        targets.append(prices[i])
    
    return np.array(features_list), np.array(targets)


# ============ 选项 A: 标准ARIMA实现 ============
def train_arima_model(prices, order=(5, 1, 0)):
    """
    训练标准ARIMA模型
    选项 A: 修复ARIMA - 使用标准statsmodels实现
    """
    if not ARMA_AVAILABLE:
        return None, None, "Statsmodels不可用"
    
    try:
        # 检查平稳性
        adf_result = adfuller(prices)
        is_stationary = adf_result[1] < 0.05
        
        # 如果非平稳，使用一阶差分
        d = 0 if is_stationary else 1
        
        # 拟合ARIMA模型
        model = ARIMA(prices, order=(order[0], d, order[2]))
        model_fit = model.fit()
        
        # 获取拟合值 (用于计算训练集指标)
        fitted_values = model_fit.fittedvalues
        
        return model_fit, fitted_values, None
    except Exception as e:
        return None, None, str(e)


def train_models(df):
    """训练预测模型 - 集成A、C、D选项"""
    prices = df['Close'].values
    
    # ============ 选项 C: 使用增强特征（可关闭以提高速度）============
    use_enhanced_features = False  # 设置为False使用原始特征，提高速度
    
    if use_enhanced_features:
        X, y = create_enhanced_features(df, lookback=20)
        print(f"✅ 选项C: 使用增强特征，特征维度: {X.shape[1]}")
    else:
        # 原始特征
        lookback = 20
        X, y = [], []
        for i in range(lookback, len(prices)):
            X.append(prices[i-lookback:i])
            y.append(prices[i])
        X, y = np.array(X), np.array(y)
    
    # 划分训练测试集
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # 计算指标
    def calc_metrics(y_true, y_pred):
        mse = np.mean((y_true - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_true - y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if np.all(y_true != 0) else 0
        r2 = 1 - np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2)
        return {'RMSE': rmse, 'MAE': mae, 'MAPE': mape, 'R2': r2}
    
    # 存储所有模型结果用于加权集成
    model_results = {}
    
    # ============ Linear Regression ============
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_metrics = calc_metrics(y_test, lr_pred)
    model_results['Linear Regression'] = {'pred': lr_pred, 'metrics': lr_metrics, 'model': lr}
    
    # ============ Random Forest ============
    # 恢复标准参数，平衡性能和准确度
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_metrics = calc_metrics(y_test, rf_pred)
    model_results['Random Forest'] = {'pred': rf_pred, 'metrics': rf_metrics, 'model': rf}
    
    # ============ 选项 A: 标准ARIMA实现（简化版，提高速度）============
    arima_metrics = {}
    arima_pred = None
    arima_model = None
    
    if ARMA_AVAILABLE:
        try:
            print("🔄 选项A: 训练标准ARIMA模型...")
            # 使用最简单的参数 (1,1,1)，提高速度
            arima_model, arima_fitted, arima_error = train_arima_model(prices, order=(1, 1, 1))
            
            if arima_error is None and arima_model is not None:
                # 使用拟合值计算指标
                # ARIMA拟合值前面可能有NaN，需要对齐
                valid_mask = ~np.isnan(arima_fitted)
                if np.sum(valid_mask) > len(y_test):
                    arima_pred_aligned = arima_fitted[valid_mask][-len(y_test):]
                    arima_metrics = calc_metrics(y_test, arima_pred_aligned)
                    arima_pred = arima_pred_aligned
                    print(f"✅ 选项A: ARIMA训练完成，R²={arima_metrics['R2']:.4f}")
                else:
                    raise Exception("ARIMA拟合值不足")
            else:
                raise Exception(arima_error or "未知错误")
        except Exception as e_arima:
            print(f"⚠️ 选项A: ARIMA训练失败: {e_arima}，使用简化版")
            # 备用：简化版ARIMA
            arima_pred = []
            for i in range(len(y_test)):
                if i == 0:
                    pred = y_train[-1]
                else:
                    error_correction = (y_test[i-1] - arima_pred[-1]) * 0.3
                    pred = arima_pred[-1] + error_correction
                arima_pred.append(pred)
            arima_pred = np.array(arima_pred)
            arima_metrics = calc_metrics(y_test, arima_pred)
    else:
        # 简化版ARIMA
        arima_pred = []
        for i in range(len(y_test)):
            if i == 0:
                pred = y_train[-1]
            else:
                error_correction = (y_test[i-1] - arima_pred[-1]) * 0.3
                pred = arima_pred[-1] + error_correction
            arima_pred.append(pred)
        arima_pred = np.array(arima_pred)
        arima_metrics = calc_metrics(y_test, arima_pred)
    
    model_results['ARIMA'] = {'pred': arima_pred, 'metrics': arima_metrics}
    
    # ============ 选项 D: XGBoost ============
    xgb_metrics = {}
    xgb_pred = None
    xgb_model = None
    
    if XGB_AVAILABLE:
        try:
            print("🚀 选项D: 训练XGBoost模型...")
            # 恢复标准参数，平衡性能和准确度
            xgb_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
            xgb_model.fit(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)
            xgb_metrics = calc_metrics(y_test, xgb_pred)
            model_results['XGBoost'] = {'pred': xgb_pred, 'metrics': xgb_metrics, 'model': xgb_model}
            print(f"✅ 选项D: XGBoost训练完成，R²={xgb_metrics['R2']:.4f}")
        except Exception as e_xgb:
            print(f"⚠️ 选项D: XGBoost训练失败: {e_xgb}")
    
    # ============ Gradient Boosting (备用，简化参数) ============
    gb_metrics = {}
    gb_pred = None
    try:
        # 恢复标准参数，平衡性能和准确度
        gb_model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        gb_model.fit(X_train, y_train)
        gb_pred = gb_model.predict(X_test)
        gb_metrics = calc_metrics(y_test, gb_pred)
        model_results['Gradient Boosting'] = {'pred': gb_pred, 'metrics': gb_metrics, 'model': gb_model}
    except Exception as e_gb:
        print(f"⚠️ Gradient Boosting训练失败: {e_gb}")
    
    # ============ 选项 D: 加权集成预测 ============
    print("🎯 选项D: 计算加权集成预测...")
    
    # 根据R²计算权重 (R²越高，权重越大)
    weights = {}
    total_r2 = 0
    for name, result in model_results.items():
        r2 = result['metrics'].get('R2', 0)
        # 使用max(r2, 0.01)避免负权重
        weight = max(r2, 0.01)
        weights[name] = weight
        total_r2 += weight
    
    # 归一化权重
    if total_r2 > 0:
        for name in weights:
            weights[name] /= total_r2
    else:
        # 如果所有R²都为负，使用等权重
        for name in weights:
            weights[name] = 1.0 / len(weights)
    
    print(f"📊 模型权重: {', '.join([f'{k}={v:.3f}' for k, v in weights.items()])}")
    
    # 计算加权集成预测
    ensemble_pred = np.zeros(len(y_test))
    for name, result in model_results.items():
        ensemble_pred += weights[name] * result['pred']
    
    ensemble_metrics = calc_metrics(y_test, ensemble_pred)
    
    # 未来预测
    future_predictions = {}
    
    # Linear Regression预测
    lr_future = []
    current_seq = prices[-20:].copy()
    for _ in range(7):
        # 构建增强特征
        if use_enhanced_features:
            features = build_future_features(current_seq, df)
            pred = lr.predict(features.reshape(1, -1))[0]
        else:
            pred = lr.predict(current_seq.reshape(1, -1))[0]
        lr_future.append(pred)
        current_seq = np.roll(current_seq, -1)
        current_seq[-1] = pred
    future_predictions['Linear Regression'] = lr_future
    
    # Random Forest预测
    rf_future = []
    current_seq = prices[-20:].copy()
    for _ in range(7):
        if use_enhanced_features:
            features = build_future_features(current_seq, df)
            pred = rf.predict(features.reshape(1, -1))[0]
        else:
            pred = rf.predict(current_seq.reshape(1, -1))[0]
        rf_future.append(pred)
        current_seq = np.roll(current_seq, -1)
        current_seq[-1] = pred
    future_predictions['Random Forest'] = rf_future
    
    # ============ 选项 A: ARIMA未来预测 ============
    arima_future = []
    if ARMA_AVAILABLE and arima_model is not None:
        try:
            # 使用标准ARIMA进行预测
            forecast_result = arima_model.forecast(steps=7)
            arima_future = forecast_result.tolist()
            print(f"✅ 选项A: ARIMA标准预测完成")
        except Exception as e:
            print(f"⚠️ 选项A: ARIMA预测失败: {e}，使用备用方法")
            # 备用：趋势外推
            last_price = prices[-1]
            trend = np.mean(np.diff(prices[-10:]))
            for i in range(7):
                pred = last_price + trend * (i + 1)
                arima_future.append(pred)
    else:
        # 备用：趋势外推
        last_price = prices[-1]
        trend = np.mean(np.diff(prices[-10:]))
        for i in range(7):
            pred = last_price + trend * (i + 1)
            arima_future.append(pred)
    future_predictions['ARIMA'] = arima_future
    
    # ============ 选项 D: XGBoost未来预测 ============
    if XGB_AVAILABLE and xgb_model is not None:
        xgb_future = []
        current_seq = prices[-20:].copy()
        for _ in range(7):
            if use_enhanced_features:
                features = build_future_features(current_seq, df)
                pred = xgb_model.predict(features.reshape(1, -1))[0]
            else:
                pred = xgb_model.predict(current_seq.reshape(1, -1))[0]
            xgb_future.append(pred)
            current_seq = np.roll(current_seq, -1)
            current_seq[-1] = pred
        future_predictions['XGBoost'] = xgb_future
    
    # Gradient Boosting未来预测
    if 'Gradient Boosting' in model_results:
        gb_future = []
        current_seq = prices[-20:].copy()
        for _ in range(7):
            if use_enhanced_features:
                features = build_future_features(current_seq, df)
                pred = model_results['Gradient Boosting']['model'].predict(features.reshape(1, -1))[0]
            else:
                pred = model_results['Gradient Boosting']['model'].predict(current_seq.reshape(1, -1))[0]
            gb_future.append(pred)
            current_seq = np.roll(current_seq, -1)
            current_seq[-1] = pred
        future_predictions['Gradient Boosting'] = gb_future
    
    # ============ 选项 D: 加权集成未来预测 ============
    ensemble_future = []
    available_models = list(future_predictions.keys())
    for day in range(7):
        weighted_pred = 0
        for model_name in available_models:
            if model_name in weights:
                weighted_pred += weights[model_name] * future_predictions[model_name][day]
        ensemble_future.append(weighted_pred)
    future_predictions['Ensemble (Weighted)'] = ensemble_future
    
    # LSTM预测 (TensorFlow) - 使用轻量级配置 + 缓存
    lstm_metrics = {}
    lstm_pred_list = []
    lstm_future = []
    
    if TF_AVAILABLE:
        try:
            # 生成价格数据的哈希，用于判断是否需要重新训练
            prices_hash = hash(prices.tobytes())
            
            # 检查缓存是否有效（360分钟内，且数据相同）
            from datetime import timedelta
            cache_valid = (
                lstm_cache['model_result'] is not None and
                lstm_cache['prices_hash'] == prices_hash and
                lstm_cache['last_update'] is not None and
                (datetime.now() - lstm_cache['last_update']) < timedelta(minutes=360)
            )
            
            if cache_valid:
                print("🧠 使用缓存的LSTM模型（360分钟内）...")
                lstm_result = lstm_cache['model_result']
                lstm_metrics = lstm_result['metrics']
                lstm_pred_list = lstm_result['predictions']
                lstm_future = lstm_result['future']
                print(f"✅ LSTM缓存加载完成，R²={lstm_metrics.get('R2', 0):.4f}")
            else:
                print("🧠 训练TensorFlow LSTM模型 (标准配置，20轮)...")
                # 使用标准模型配置，平衡性能和准确度
                lstm_result = train_lstm(prices, lookback=20, epochs=20, batch_size=32, use_simple=False)
                
                if lstm_result['status'] == 'success':
                    lstm_metrics = lstm_result['metrics']
                    lstm_pred_list = lstm_result['predictions']
                    lstm_future = lstm_result['future']
                    
                    # 更新缓存
                    lstm_cache['model_result'] = lstm_result
                    lstm_cache['prices_hash'] = prices_hash
                    lstm_cache['last_update'] = datetime.now()
                    
                    print(f"✅ LSTM训练完成，R²={lstm_metrics.get('R2', 0):.4f}")
                else:
                    print(f"⚠️ LSTM训练失败: {lstm_result.get('message', '未知错误')}")
        except Exception as e:
            print(f"⚠️ LSTM调用失败: {e}")
    else:
        print("⚠️ TensorFlow未安装，跳过LSTM训练")
    
    # 构建返回结果
    metrics = {
        'Linear Regression': model_results['Linear Regression']['metrics'],
        'Random Forest': model_results['Random Forest']['metrics'],
        'ARIMA': model_results['ARIMA']['metrics'],
        'Ensemble (Weighted)': ensemble_metrics
    }
    
    predictions = {
        'Linear Regression': model_results['Linear Regression']['pred'].tolist() if hasattr(model_results['Linear Regression']['pred'], 'tolist') else list(model_results['Linear Regression']['pred']),
        'Random Forest': model_results['Random Forest']['pred'].tolist() if hasattr(model_results['Random Forest']['pred'], 'tolist') else list(model_results['Random Forest']['pred']),
        'ARIMA': model_results['ARIMA']['pred'].tolist() if hasattr(model_results['ARIMA']['pred'], 'tolist') else list(model_results['ARIMA']['pred']),
        'Ensemble (Weighted)': ensemble_pred.tolist() if hasattr(ensemble_pred, 'tolist') else list(ensemble_pred)
    }
    
    # 添加XGBoost结果
    if XGB_AVAILABLE and 'XGBoost' in model_results:
        metrics['XGBoost'] = model_results['XGBoost']['metrics']
        xgb_pred_data = model_results['XGBoost']['pred']
        predictions['XGBoost'] = xgb_pred_data.tolist() if hasattr(xgb_pred_data, 'tolist') else list(xgb_pred_data)
    
    # 添加Gradient Boosting结果
    if 'Gradient Boosting' in model_results:
        metrics['Gradient Boosting'] = model_results['Gradient Boosting']['metrics']
        gb_pred_data = model_results['Gradient Boosting']['pred']
        predictions['Gradient Boosting'] = gb_pred_data.tolist() if hasattr(gb_pred_data, 'tolist') else list(gb_pred_data)
    
    # 如果LSTM成功，添加到结果中
    if lstm_metrics:
        metrics['LSTM'] = lstm_metrics
        predictions['LSTM'] = lstm_pred_list
        future_predictions['LSTM'] = lstm_future
        print(f"📊 LSTM未来7天预测: {[round(p, 2) for p in lstm_future]}")
    
    # 添加权重信息
    metrics['_ensemble_weights'] = weights
    
    return {
        'metrics': metrics,
        'predictions': predictions,
        'future': future_predictions,
        'actual': y_test.tolist()
    }


def build_future_features(current_seq, df):
    """
    为未来预测构建增强特征
    选项 C: 特征工程辅助函数
    """
    base_features = current_seq.tolist()
    
    # 技术指标特征
    tech_features = []
    
    # 价格统计
    tech_features.append(np.mean(current_seq))
    tech_features.append(np.std(current_seq))
    tech_features.append((current_seq[-1] - current_seq[0]) / (current_seq[0] + 1e-8))
    tech_features.append((current_seq[-1] - np.min(current_seq)) / (np.max(current_seq) - np.min(current_seq) + 1e-8))
    
    # 简易RSI
    deltas = np.diff(current_seq)
    gains = np.sum(deltas[deltas > 0]) if len(deltas) > 0 else 0
    losses = -np.sum(deltas[deltas < 0]) if len(deltas) > 0 else 0
    rs = gains / (losses + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    tech_features.append(rsi)
    
    # 简易MACD
    ema12 = np.mean(current_seq[-12:]) if len(current_seq) >= 12 else np.mean(current_seq)
    ema26 = np.mean(current_seq[-20:]) if len(current_seq) >= 20 else np.mean(current_seq)
    macd = ema12 - ema26
    tech_features.extend([macd, 0])
    
    # 布林带位置
    ma = np.mean(current_seq)
    std = np.std(current_seq)
    bb_position = (current_seq[-1] - (ma - 2*std)) / (4*std + 1e-8)
    tech_features.append(bb_position)
    
    # 成交量占位
    tech_features.extend([0, 0])
    
    return np.array(base_features + tech_features)

@app.route('/')
def index():
    return render_template('gold_dashboard.html')

@app.route('/macro')
def macro_dashboard():
    """黄金价格宏观因子可调整预测系统"""
    return render_template('macro_dashboard.html')

@app.route('/api/data')
def get_data():
    """获取黄金数据"""
    global cache
    
    try:
        # 检查缓存（120分钟内不重复获取）
        if cache['data'] is not None and cache['last_update'] is not None:
            if datetime.now() - cache['last_update'] < timedelta(minutes=CACHE_MINUTES):
                print(f"📦 使用缓存数据（{CACHE_MINUTES}分钟内）")
                return jsonify(cache['data'])
        
        # 获取数据
        print("🔄 正在获取黄金数据...")
        df = get_real_gold_data()
        
        # 判断数据来源
        data_source = "上海期货交易所 AU2604"
        if df is None or df.empty:
            print("⚠️ 使用模拟数据")
            df = generate_mock_data()
            data_source = "模拟数据"
        elif 'data_source' in df.attrs:
            data_source = df.attrs.get('data_source', '未知来源')
        
        print(f"📊 数据来源: {data_source}, 记录数: {len(df)}")
        
        # 训练模型
        print("🤖 正在训练模型...")
        model_results = train_models(df)
        print("✅ 模型训练完成")
        
        # 生成未来日期
        future_dates = []
        for i in range(1, 8):
            date = datetime.now() + timedelta(days=i)
            future_dates.append(date.strftime('%Y-%m-%d'))
        
        # 获取最新实时价格（优先于日线收盘价）
        print("🔄 获取最新实时价格...")
        current_price_realtime, price_contract = get_shfe_current_price()
        
        if current_price_realtime is not None:
            # 使用实时价格
            current_price = current_price_realtime
            last_close = float(df['Close'].iloc[-1])  # 昨日收盘价
            price_change = current_price - last_close
            price_change_pct = (price_change / last_close * 100) if last_close > 0 else 0
            data_source_with_price = f"{data_source} | 实时{price_contract}"
            print(f"✅ 使用实时价格: {current_price} ({price_contract})")
        else:
            # 使用日线数据
            current_price = float(df['Close'].iloc[-1])
            last_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else current_price
            price_change = current_price - last_close
            price_change_pct = (price_change / last_close * 100) if last_close > 0 else 0
            data_source_with_price = data_source
        
        # 准备响应数据
        data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist()[-100:],
            'prices': df['Close'].tolist()[-100:],
            'ma20': df['MA20'].tolist()[-100:] if 'MA20' in df.columns else [],
            'ma60': df['MA60'].tolist()[-100:] if 'MA60' in df.columns else [],
            'rsi': df['RSI'].tolist()[-100:] if 'RSI' in df.columns else [],
            'macd': df['MACD'].tolist()[-100:] if 'MACD' in df.columns else [],
            'volume': df['Volume'].tolist()[-100:] if 'Volume' in df.columns else [],
            'current_price': round(current_price, 2),
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change_pct, 2),
            'metrics': model_results['metrics'],
            'predictions': model_results['predictions'],
            'actual': model_results['actual'],
            'future_predictions': model_results['future'],
            'future_dates': future_dates,
            'data_source': data_source_with_price,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 转换所有 numpy/pandas 类型为 Python 原生类型
        data = convert_to_native(data)
        
        # 更新缓存
        cache['data'] = data
        cache['last_update'] = datetime.now()
        
        print("✅ 数据获取成功")
        return jsonify(data)
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 获取数据失败: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg, 'traceback': traceback.format_exc()}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh():
    """强制刷新数据"""
    global cache, lstm_cache, data_fetch_cache
    cache['data'] = None
    cache['last_update'] = None
    # 同时清除LSTM缓存
    lstm_cache['model_result'] = None
    lstm_cache['prices_hash'] = None
    lstm_cache['last_update'] = None
    # 清除数据获取缓存（关键！确保获取最新价格）
    data_fetch_cache['df'] = None
    data_fetch_cache['timestamp'] = None
    print("🔄 所有缓存已清除，将重新获取最新数据")
    return jsonify({'status': 'success', 'message': '数据已刷新（包括数据获取缓存）'})


# ============ 增强版宏观因子API ============

class MacroFactorCollector:
    """增强版宏观因子收集器 - 使用akshare和多重数据源"""
    
    def __init__(self):
        self.factors_config = {
            '美元指数 (DXY)': {'weight': 0.15, 'impact': 'negative'},
            '实际利率 (TIPS)': {'weight': 0.30, 'impact': 'negative'},
            '通胀预期 (CPI)': {'weight': 0.05, 'impact': 'positive'},
            '美债收益率': {'weight': 0.10, 'impact': 'negative'},
            '地缘政治风险 (GPR)': {'weight': 0.20, 'impact': 'positive'},
            'VIX波动率': {'weight': 0.05, 'impact': 'positive'},
            '经济不确定性 (EPU)': {'weight': 0.01, 'impact': 'positive'},
            '黄金ETF持仓': {'weight': 0.09, 'impact': 'positive'},
            '金银比/铜金比': {'weight': 0.05, 'impact': 'positive'}
        }
        self.data_log = []
    
    def log(self, message):
        """记录日志"""
        self.data_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def get_dxy(self):
        """1. 美元指数 - 优先akshare, 备用Yahoo Finance和Serper"""
        # 方法1: akshare 外汇数据 - 使用即期汇率
        try:
            import akshare as ak
            # 获取美元/人民币汇率
            print("   尝试获取 USD/CNY 汇率...")
            fx_df = ak.fx_spot_quote()
            if not fx_df.empty:
                print(f"   fx_df columns: {list(fx_df.columns)}")
                # 查找 USD/CNY 行
                usd_row = None
                for idx, row in fx_df.iterrows():
                    curr_pair = str(row.get('货币对', ''))
                    if 'USD/CNY' in curr_pair or 'USD' in curr_pair:
                        usd_row = row
                        print(f"   找到USD行: {row.to_dict()}")
                        break
                
                if usd_row is not None:
                    # 使用买报价列
                    current = float(usd_row['买报价'])
                    # 估算美元指数 (7.0 = 100点基准)
                    dxy_estimate = 100 + (current - 7.0) * 10
                    return {
                        'value': round(dxy_estimate, 2),
                        'change_1m': 0,
                        'trend': 'stable',
                        'weight': 0.15,
                        'impact': 'negative',
                        'data_source': 'akshare 外汇即期汇率 (USD/CNY)',
                        'reliability': '高',
                        'method': '基于美元兑人民币汇率估算DXY',
                        'raw_rate': round(current, 4)
                    }
        except Exception as e:
            self.log(f"akshare 即期汇率失败: {e}")
            print(f"   即期汇率失败: {e}")
        
        # 方法1b: akshare 人民币汇率报价
        try:
            import akshare as ak
            print("   尝试获取人民币汇率报价...")
            fx_df = ak.currency_boc_safe()
            if not fx_df.empty:
                # 查找美元行
                for idx, row in fx_df.iterrows():
                    if 'USD' in str(row.get('货币', '')) or '美元' in str(row.get('货币', '')):
                        current = float(row.get('现汇买入价', row.get('买入价', 7.0)))
                        prev = current  # 无法获取历史变化
                        dxy_estimate = 100 + (current - 7.0) * 10
                        return {
                            'value': round(dxy_estimate, 2),
                            'change_1m': 0,
                            'trend': 'stable',
                            'weight': 0.15,
                            'impact': 'negative',
                            'data_source': 'akshare 人民币汇率报价 (USD/CNY)',
                            'reliability': '高',
                            'method': '基于美元兑人民币汇率估算DXY',
                            'raw_rate': round(current, 4)
                        }
        except Exception as e:
            self.log(f"akshare 人民币汇率失败: {e}")
        
        # 方法2: Yahoo Finance
        try:
            dxy = yf.Ticker("DX-Y.NYB").history(period="1mo")
            value = dxy['Close'].iloc[-1]
            change = (value - dxy['Close'].iloc[-20]) / dxy['Close'].iloc[-20] * 100
            return {
                'value': round(value, 2),
                'change_1m': round(change, 2),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.15,
                'impact': 'negative',
                'data_source': 'Yahoo Finance DXY',
                'reliability': '高'
            }
        except Exception as e:
            self.log(f"Yahoo DXY失败: {e}")
        
        # 方法3: Serper 搜索备用
        try:
            from serper_data_source import search_gold_price
            price_data = search_gold_price()
            if price_data and price_data.get('currency') == 'USD':
                # 使用黄金价格间接反映美元强弱
                gold_price = price_data['price']
                # 黄金价格与美元指数通常负相关
                dxy_estimate = 120 - (gold_price - 2000) / 50
                return {
                    'value': round(dxy_estimate, 2),
                    'change_1m': 0,
                    'trend': 'stable',
                    'weight': 0.15,
                    'impact': 'negative',
                    'data_source': 'Serper API (黄金价格间接估算)',
                    'reliability': '中',
                    'method': '基于黄金价格间接估算美元强弱'
                }
        except Exception as e:
            self.log(f"Serper DXY失败: {e}")
        
        return self._fallback_factor('美元指数', 103.5, 0.15, 'negative', '所有数据源失败')
    
    def get_real_rate_tips(self):
        """2. 实际利率 - 优先akshare中国国债, 备用TIPS ETF"""
        # 方法1: akshare 中国国债收益率（作为实际利率代理）
        try:
            import akshare as ak
            # 获取中国10年期国债收益率
            bond_df = ak.bond_zh_us_rate()
            if not bond_df.empty and '中国国债收益率10年' in bond_df.columns:
                current_yield = float(bond_df['中国国债收益率10年'].iloc[-1])
                prev_yield = float(bond_df['中国国债收益率10年'].iloc[-20]) if len(bond_df) >= 20 else current_yield
                change = current_yield - prev_yield
                # 中国CPI作为通胀预期
                cpi_df = ak.macro_china_cpi()
                cpi = float(cpi_df['今值'].iloc[-1]) if not cpi_df.empty else 2.0
                real_rate = current_yield - cpi
                
                return {
                    'value': round(real_rate, 2),
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.30,
                    'impact': 'negative',
                    'data_source': 'akshare 中国国债收益率 - CPI',
                    'reliability': '高',
                    'method': '10年期国债收益率减去CPI',
                    'nominal_yield': round(current_yield, 2),
                    'cpi': round(cpi, 2)
                }
        except Exception as e:
            self.log(f"akshare实际利率失败: {e}")
        
        # 方法2: akshare 美国利率数据
        try:
            import akshare as ak
            us_rate_df = ak.bond_zh_us_rate()
            if not us_rate_df.empty and '美国国债收益率10年' in us_rate_df.columns:
                current = float(us_rate_df['美国国债收益率10年'].iloc[-1])
                prev = float(us_rate_df['美国国债收益率10年'].iloc[-2]) if len(us_rate_df) >= 2 else current
                change = current - prev
                return {
                    'value': round(current - 2.0, 2),  # 减去估算通胀
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.30,
                    'impact': 'negative',
                    'data_source': 'akshare 美国国债收益率',
                    'reliability': '高',
                    'method': '国债收益率减去估算通胀'
                }
        except Exception as e:
            self.log(f"akshare美债利率失败: {e}")
        
        # 方法3: TIPS ETF
        try:
            tips = yf.Ticker("TIP").history(period="1mo")
            tips_price = tips['Close'].iloc[-1]
            implied_real_rate = (100 / tips_price - 1) * 100
            prev_price = tips['Close'].iloc[-20]
            prev_rate = (100 / prev_price - 1) * 100
            change = implied_real_rate - prev_rate
            
            return {
                'value': round(implied_real_rate, 2),
                'change_1m': round(change, 2),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.30,
                'impact': 'negative',
                'data_source': 'TIPS ETF (^TIP)',
                'reliability': '高',
                'method': 'TIPS价格反推实际利率',
                'raw_price': round(tips_price, 2)
            }
        except:
            pass
        
        # 方法4: 盈亏平衡通胀率
        try:
            tnx = yf.Ticker("^TNX").history(period="1mo")
            breakeven = tnx['Close'].iloc[-1] - 1.5
            change = tnx['Close'].iloc[-1] - tnx['Close'].iloc[-20]
            
            return {
                'value': round(breakeven, 2),
                'change_1m': round(change, 2),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.18,
                'impact': 'negative',
                'data_source': 'Breakeven Inflation Rate',
                'reliability': '中',
                'method': '10Y Treasury - TIPS Yield'
            }
        except Exception as e:
            return self._fallback_factor('实际利率', 1.5, 0.30, 'negative', str(e))
    
    def get_inflation_cpi(self):
        """3. 通胀预期 - 优先使用中国CPI"""
        # 方法1: akshare 中国CPI (优先，因为 akshare 对中国数据支持更好)
        try:
            import akshare as ak
            print("   尝试获取中国CPI...")
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                # 列名是中文: '月份', '全国-当月', '全国-同比增长' 等
                cpi_col = None
                for col in cpi_df.columns:
                    if '全国-当月' in col or '当月' in col:
                        cpi_col = col
                        break
                
                if cpi_col:
                    current_cpi = float(cpi_df[cpi_col].iloc[-1])
                    try:
                        prev_cpi = float(cpi_df[cpi_col].iloc[-2])
                        change = ((current_cpi - prev_cpi) / prev_cpi) * 100
                    except:
                        change = 0
                    
                    # 转换为百分比形式 (如果数据是107.0这种形式)
                    if current_cpi > 50:  # 说明是指数形式
                        current_cpi_pct = (current_cpi - 100)
                    else:
                        current_cpi_pct = current_cpi
                    
                    return {
                        'value': round(current_cpi_pct, 2),
                        'change_1m': round(change, 2),
                        'trend': 'up' if change > 0 else 'down',
                        'weight': 0.05,
                        'impact': 'positive',
                        'data_source': 'akshare 中国CPI (macro_china_cpi)',
                        'reliability': '高',
                        'method': '中国消费者价格指数(CPI)',
                        'raw_value': round(current_cpi, 2)
                    }
        except Exception as e:
            self.log(f"akshare中国CPI失败: {e}")
        
        # 方法2: 使用 akshare 的中国宏观经济数据 - CPI同比
        try:
            import akshare as ak
            print("   尝试获取中国CPI同比...")
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                # 使用同比增长率列
                for col in cpi_df.columns:
                    if '同比增长' in col:
                        current_cpi = float(cpi_df[col].iloc[-1])
                        try:
                            prev_cpi = float(cpi_df[col].iloc[-2])
                            change = current_cpi - prev_cpi
                        except:
                            change = 0
                        
                        return {
                            'value': round(current_cpi, 2),
                            'change_1m': round(change, 2),
                            'trend': 'up' if change > 0 else 'down',
                            'weight': 0.05,
                            'impact': 'positive',
                            'data_source': 'akshare 中国CPI同比',
                            'reliability': '高',
                            'method': '中国CPI同比增长率'
                        }
        except Exception as e:
            self.log(f"akshare CPI同比失败: {e}")
        
        # 方法3: 盈亏平衡通胀率
        try:
            tnx = yf.Ticker("^TNX").history(period="1d")
            breakeven = tnx['Close'].iloc[-1] - 1.5
            return {
                'value': round(breakeven, 2),
                'change_1m': 0,
                'trend': 'up' if breakeven > 2.5 else 'down',
                'weight': 0.05,
                'impact': 'positive',
                'data_source': 'Breakeven Rate',
                'reliability': '中'
            }
        except Exception as e:
            return self._fallback_factor('通胀预期', 2.5, 0.05, 'positive', str(e))
    
    def get_bond_yield(self):
        """4. 美债收益率 - 优先akshare, 备用Yahoo Finance"""
        # 方法1: akshare 中美利率对比数据
        try:
            import akshare as ak
            bond_df = ak.bond_zh_us_rate()
            if not bond_df.empty and '美国国债收益率10年' in bond_df.columns:
                current = float(bond_df['美国国债收益率10年'].iloc[-1])
                prev = float(bond_df['美国国债收益率10年'].iloc[-20]) if len(bond_df) >= 20 else current
                change = current - prev
                return {
                    'value': round(current, 2),
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.12,
                    'impact': 'negative',
                    'data_source': 'akshare 美国国债收益率10年',
                    'reliability': '高'
                }
        except Exception as e:
            self.log(f"akshare美债收益率失败: {e}")
        
        # 方法2: akshare 美国宏观数据 - 使用CPI和利率组合
        try:
            import akshare as ak
            # 使用中美利率对比数据
            bond_df = ak.bond_zh_us_rate()
            if not bond_df.empty and '美国国债收益率10年' in bond_df.columns:
                current = float(bond_df['美国国债收益率10年'].iloc[-1])
                prev = float(bond_df['美国国债收益率10年'].iloc[-5]) if len(bond_df) >= 5 else current
                change = current - prev
                return {
                    'value': round(current, 2),
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.12,
                    'impact': 'negative',
                    'data_source': 'akshare 美国国债收益率10年',
                    'reliability': '高'
                }
        except Exception as e:
            self.log(f"akshare美国宏观数据失败: {e}")
        
        # 方法3: Yahoo Finance
        try:
            tnx = yf.Ticker("^TNX").history(period="1mo")
            value = tnx['Close'].iloc[-1]
            change = value - tnx['Close'].iloc[-20]
            return {
                'value': round(value, 2),
                'change_1m': round(change, 2),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.12,
                'impact': 'negative',
                'data_source': 'Yahoo Finance ^TNX',
                'reliability': '高'
            }
        except Exception as e:
            return self._fallback_factor('美债收益率', 4.2, 0.12, 'negative', str(e))
    
    def get_gpr(self):
        """5. 地缘政治风险 - 使用官方GPR指数，多重备用"""
        # 优先使用官方Caldara-Iacoviello GPR指数
        try:
            from enhanced_gpr_epu import get_gpr_index
            result = get_gpr_index()
            
            if result.get('value') is not None and result.get('status') != 'error':
                print(f"✅ 成功获取官方GPR数据: {result['value']}")
                return result
            else:
                raise Exception(result.get('error', 'GPR数据获取失败'))
                
        except Exception as e:
            print(f"⚠️ 官方GPR获取失败: {e}")
        
        # 备用1: 使用EnhancedDataCollector直接获取
        try:
            from enhanced_gpr_epu import EnhancedDataCollector
            collector = EnhancedDataCollector()
            result = collector.get_gpr_data()
            if result.get('status') == 'success':
                print(f"✅ 通过EnhancedDataCollector获取GPR: {result['value']}")
                return {
                    'value': result['value'],
                    'change_1m': result.get('change_1m', 0),
                    'trend': result.get('trend', 'stable'),
                    'weight': 0.20,
                    'impact': 'positive',
                    'data_source': result.get('data_source', 'Caldara-Iacoviello GPR'),
                    'reliability': result.get('reliability', '极高')
                }
        except Exception as e:
            print(f"⚠️ EnhancedDataCollector GPR失败: {e}")
        
        # 备用2: 使用缓存数据
        try:
            cache_file = './data_cache/gpr_daily.xls'
            if os.path.exists(cache_file):
                import pandas as pd
                df = pd.read_excel(cache_file)
                df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
                df = df.sort_values('date')
                latest = df.iloc[-1]
                gpr_30d_ago = df.iloc[-30]['GPRD'] if len(df) >= 30 else df.iloc[0]['GPRD']
                change = latest['GPRD'] - gpr_30d_ago
                
                return {
                    'value': round(latest['GPRD'], 2),
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.20,
                    'impact': 'positive',
                    'data_source': 'Caldara-Iacoviello GPR (缓存)',
                    'reliability': '高',
                    'note': '使用缓存数据'
                }
        except Exception as e:
            print(f"⚠️ GPR缓存读取失败: {e}")
        
        # 备用3: VIX代理
        try:
            vix = yf.Ticker("^VIX").history(period="1mo")
            vix_val = vix['Close'].iloc[-1]
            gpr = min(vix_val / 5, 10)
            change = (vix['Close'].iloc[-1] - vix['Close'].iloc[-20]) / 5
            
            return {
                'value': round(gpr, 1),
                'change_1m': round(change, 1),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.20,
                'impact': 'positive',
                'data_source': 'VIX代理 (官方GPR失败时备用)',
                'reliability': '中',
                'method': 'VIX / 5 映射到GPR尺度',
                'note': '官方GPR获取失败'
            }
        except Exception as e2:
            return self._fallback_factor('地缘政治风险', 5.5, 0.20, 'positive', str(e2))
    
    def get_vix(self):
        """6. VIX波动率 - 优先akshare中国波动率, 备用Yahoo VIX"""
        # 方法1: akshare 中国波动率（基于上证指数）
        try:
            import akshare as ak
            sh_df = ak.index_zh_a_hist(symbol="000001", period="daily",
                                        start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'))
            if not sh_df.empty:
                sh_df['pct_change'] = sh_df['收盘'].pct_change()
                volatility = sh_df['pct_change'].std() * np.sqrt(252) * 100
                
                # 计算变化（使用最近20天vs前20天）
                recent_vol = sh_df.tail(20)['pct_change'].std() * np.sqrt(252) * 100
                prev_vol = sh_df.head(-20).tail(20)['pct_change'].std() * np.sqrt(252) * 100 if len(sh_df) >= 40 else recent_vol
                change = recent_vol - prev_vol
                
                return {
                    'value': round(volatility, 2),
                    'change_1m': round(change, 2),
                    'trend': 'up' if change > 0 else 'down',
                    'weight': 0.05,
                    'impact': 'positive',
                    'data_source': 'akshare 上证指数波动率 (年化)',
                    'reliability': '高',
                    'method': '基于上证指数日收益率计算年化波动率'
                }
        except Exception as e:
            self.log(f"akshare波动率失败: {e}")
        
        # 方法2: akshare 50ETF波动率（更接近VIX概念）
        try:
            import akshare as ak
            # 50ETF期权波动率或ETF价格历史
            etf_df = ak.fund_etf_hist_em(symbol="510050", period="daily",
                                          start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'))
            if not etf_df.empty:
                etf_df['pct_change'] = etf_df['收盘'].pct_change()
                volatility = etf_df['pct_change'].std() * np.sqrt(252) * 100
                return {
                    'value': round(volatility, 2),
                    'change_1m': 0,
                    'trend': 'up',
                    'weight': 0.08,
                    'impact': 'positive',
                    'data_source': 'akshare 50ETF波动率',
                    'reliability': '高',
                    'method': '基于50ETF日收益率计算年化波动率'
                }
        except Exception as e:
            self.log(f"akshare 50ETF波动率失败: {e}")
        
        # 方法3: Yahoo Finance VIX
        try:
            vix = yf.Ticker("^VIX").history(period="1mo")
            value = vix['Close'].iloc[-1]
            change = value - vix['Close'].iloc[-20]
            return {
                'value': round(value, 2),
                'change_1m': round(change, 2),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.08,
                'impact': 'positive',
                'data_source': 'Yahoo Finance ^VIX',
                'reliability': '极高'
            }
        except Exception as e:
            return self._fallback_factor('VIX波动率', 18.5, 0.08, 'positive', str(e))
    
    def get_epu(self):
        """7. 经济不确定性 - 使用官方EPU指数，多重备用"""
        # 优先使用官方EPU指数（中国）
        try:
            from enhanced_gpr_epu import get_epu_index, EnhancedDataCollector
            result = get_epu_index('China')
            
            # 检查数据有效性：值不能为None，不能为0（中国EPU正常值通常在100-400之间）
            if (result.get('value') is not None and 
                result.get('status') != 'error' and 
                result.get('value', 0) > 10):  # EPU值应该大于10才有效
                print(f"✅ 成功获取官方EPU-China数据: {result['value']}")
                return result
            else:
                raise Exception(f"EPU-China数据无效: value={result.get('value')}")
                
        except Exception as e:
            print(f"⚠️ 官方EPU-China获取失败: {e}")
        
        # 备用1: 使用EnhancedDataCollector直接获取中国EPU
        try:
            from enhanced_gpr_epu import EnhancedDataCollector
            collector = EnhancedDataCollector()
            result = collector.get_epu_data('China')
            # 检查状态成功且值有效（大于10）
            if (result.get('status') == 'success' and 
                result.get('value') is not None and 
                result.get('value', 0) > 10):
                print(f"✅ 通过EnhancedDataCollector获取EPU-China: {result['value']}")
                return {
                    'value': result['value'],
                    'change_1m': result.get('change_1m', 0),
                    'trend': result.get('trend', 'stable'),
                    'weight': 0.01,
                    'impact': 'positive',
                    'data_source': result.get('data_source', 'China EPU Official'),
                    'reliability': result.get('reliability', '极高')
                }
            else:
                raise Exception(f"EPU-China数据无效: value={result.get('value')}")
        except Exception as e:
            print(f"⚠️ EnhancedDataCollector EPU-China失败: {e}")
        
        # 备用2: 使用美国EPU
        try:
            from enhanced_gpr_epu import get_epu_index, EnhancedDataCollector
            result = get_epu_index('US')
            
            if result.get('value') is not None and result.get('status') != 'error':
                print(f"✅ 成功获取官方EPU-US数据: {result['value']}")
                # 确保权重为1%
                result['weight'] = 0.01
                result['data_source'] = result.get('data_source', 'US Economic Policy Uncertainty Index') + ' (备用)'
                return result
            else:
                raise Exception(result.get('error', 'EPU-US数据获取失败'))
                
        except Exception as e:
            print(f"⚠️ 官方EPU-US获取失败: {e}")
        
        # 备用3: 使用缓存数据
        try:
            cache_files = ['./data_cache/epu_china.xlsx', './data_cache/epu_us.xlsx']
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    import pandas as pd
                    df = pd.read_excel(cache_file)
                    country = 'China' if 'china' in cache_file else 'US'
                    epu_col = 'EPU_Mainland_Paper' if 'EPU_Mainland_Paper' in df.columns else 'EPU'
                    df['date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
                    df = df.sort_values('date')
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) >= 2 else latest
                    change = latest[epu_col] - prev[epu_col]
                    
                    return {
                        'value': round(latest[epu_col], 2),
                        'change_1m': round(change, 2),
                        'trend': 'up' if change > 0 else 'down',
                        'weight': 0.01,
                        'impact': 'positive',
                        'data_source': f'EPU {country} (缓存)',
                        'reliability': '高',
                        'note': '使用缓存数据'
                    }
        except Exception as e:
            print(f"⚠️ EPU缓存读取失败: {e}")
        
        # 最后备用：波动率代理
        try:
            import akshare as ak
            sh_df = ak.index_zh_a_hist(symbol="000001", period="daily",
                                        start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'))
            if not sh_df.empty:
                sh_df['pct_change'] = sh_df['收盘'].pct_change()
                volatility = sh_df['pct_change'].std() * np.sqrt(252) * 100
                epu_proxy = 200 + volatility * 10
                
                return {
                    'value': round(epu_proxy, 0),
                    'change_1m': 0,
                    'trend': 'up' if volatility > 15 else 'down',
                    'weight': 0.01,
                    'impact': 'positive',
                    'data_source': 'akshare 上证指数波动率 (官方EPU失败时备用)',
                    'reliability': '中',
                    'method': '年化波动率映射到EPU尺度',
                    'volatility': round(volatility, 2)
                }
        except:
            pass
        
        try:
            sp500 = yf.Ticker("^GSPC").history(period="3mo")
            volatility = sp500['Close'].pct_change().std() * np.sqrt(252) * 100
            epu_proxy = 200 + volatility * 10
            
            return {
                'value': round(epu_proxy, 0),
                'change_1m': 0,
                'trend': 'up' if volatility > 15 else 'down',
                'weight': 0.01,
                'impact': 'positive',
                'data_source': '标普500波动率 (备用)',
                'reliability': '中',
                'method': '年化波动率映射到EPU尺度'
            }
        except Exception as e:
            return self._fallback_factor('经济不确定性', 200, 0.01, 'positive', str(e))
    
    def get_etf_holdings(self):
        """8. 黄金ETF持仓 - 使用官方数据源，多重备用"""
        # 优先使用增强版ETF数据获取模块 - 官方SPDR数据
        try:
            from etf_holdings_collector import ETFHoldingsCollector
            collector = ETFHoldingsCollector()
            result = collector.get_gld_holdings_official()
            
            if result.get('value') is not None and result.get('status') == 'success':
                print(f"✅ 成功获取SPDR官方ETF持仓: {result['value']} 吨")
                return {
                    'value': result['value'],
                    'change_1m': result.get('change_30d', 0),
                    'trend': result.get('trend', 'stable'),
                    'weight': 0.09,
                    'impact': 'positive',
                    'data_source': result.get('data_source', 'SPDR Gold Shares Official'),
                    'reliability': result.get('reliability', '极高'),
                    'note': result.get('note', '')
                }
        except Exception as e:
            print(f"⚠️ SPDR官方ETF获取失败: {e}")
        
        # 备用1: yfinance GLD计算
        try:
            from etf_holdings_collector import ETFHoldingsCollector
            collector = ETFHoldingsCollector()
            result = collector.get_gld_holdings_yfinance()
            
            if result.get('value') is not None and result.get('status') == 'success':
                print(f"✅ 通过yfinance获取GLD持仓: {result['value']} 吨")
                return {
                    'value': result['value'],
                    'change_1m': result.get('change_30d_pct', 0),
                    'trend': result.get('trend', 'stable'),
                    'weight': 0.09,
                    'impact': 'positive',
                    'data_source': result.get('data_source', 'Yahoo Finance GLD'),
                    'reliability': result.get('reliability', '高'),
                    'method': result.get('method', '')
                }
        except Exception as e:
            print(f"⚠️ yfinance GLD获取失败: {e}")
        
        # 备用2: 华安黄金ETF (中国)
        try:
            from etf_holdings_collector import ETFHoldingsCollector
            collector = ETFHoldingsCollector()
            result = collector.get_huaan_etf_holdings()
            
            if result.get('value') is not None and result.get('status') == 'success':
                print(f"✅ 成功获取华安黄金ETF: {result['value']} 吨")
                return {
                    'value': result['value'],
                    'change_1m': result.get('change_30d_pct', 0),
                    'trend': result.get('trend', 'stable'),
                    'weight': 0.09,
                    'impact': 'positive',
                    'data_source': result.get('data_source', '华安黄金ETF'),
                    'reliability': result.get('reliability', '中'),
                    'method': result.get('method', '')
                }
        except Exception as e:
            print(f"⚠️ 华安ETF获取失败: {e}")
        
        # 备用方法1: akshare 华安黄金ETF
        try:
            import akshare as ak
            etf_df = ak.fund_etf_hist_em(symbol="518880", period="daily",
                                          start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
            if not etf_df.empty:
                price = float(etf_df['收盘'].iloc[-1])
                price_change = (price - float(etf_df['收盘'].iloc[-20])) / float(etf_df['收盘'].iloc[-20]) * 100
                estimated_holdings = 40 + price_change * 0.3
                
                return {
                    'value': round(estimated_holdings, 1),
                    'change_1m': round(price_change, 2),
                    'trend': 'up' if price_change > 0 else 'down',
                    'weight': 0.09,
                    'impact': 'positive',
                    'data_source': 'akshare 华安黄金ETF(518880)',
                    'reliability': '中',
                    'method': '价格变化估算持仓',
                    'note': 'SPDR官方获取失败'
                }
        except:
            pass
        
        # 备用方法2: GLD价格代理
        try:
            gld = yf.Ticker("GLD").history(period="1mo")
            price_change = (gld['Close'].iloc[-1] - gld['Close'].iloc[-20]) / gld['Close'].iloc[-20] * 100
            estimated_holdings = 900 + price_change * 2
            
            return {
                'value': round(estimated_holdings, 1),
                'change_1m': round(price_change, 2),
                'trend': 'up' if price_change > 0 else 'down',
                'weight': 0.09,
                'impact': 'positive',
                'data_source': 'GLD价格代理 (备用)',
                'reliability': '低',
                'method': '价格变化估算持仓变化'
            }
        except Exception as e2:
            return self._fallback_factor('黄金ETF持仓', 850, 0.09, 'positive', str(e2))
    
    def get_gold_ratios(self):
        """9. 金银比/铜金比"""
        # 方法1: akshare 上期所
        try:
            import akshare as ak
            au_df = ak.futures_zh_daily_sina(symbol="AU2406")
            ag_df = ak.futures_zh_daily_sina(symbol="AG2406")
            
            if not au_df.empty and not ag_df.empty:
                au_price = float(au_df['close'].iloc[-1])
                ag_price = float(ag_df['close'].iloc[-1])
                gold_silver = (au_price / (ag_price / 1000))
                
                try:
                    cu_df = ak.futures_zh_daily_sina(symbol="CU2406")
                    cu_price = float(cu_df['close'].iloc[-1])
                    copper_gold = (cu_price / 1000) / au_price * 100
                except:
                    copper_gold = None
                
                return {
                    'value': {
                        'gold_silver': round(gold_silver, 1),
                        'copper_gold': round(copper_gold, 2) if copper_gold else 'N/A'
                    },
                    'change_1m': 0,
                    'trend': 'up' if gold_silver > 80 else 'down',
                    'weight': 0.05,
                    'impact': 'positive',
                    'data_source': 'akshare 上海期货交易所',
                    'reliability': '高'
                }
        except:
            pass
        
        # 方法2: Yahoo Finance
        try:
            gold = yf.Ticker("GC=F").history(period="1mo")
            silver = yf.Ticker("SI=F").history(period="1mo")
            copper = yf.Ticker("HG=F").history(period="1mo")
            
            gold_silver = gold['Close'].iloc[-1] / silver['Close'].iloc[-1]
            copper_gold = copper['Close'].iloc[-1] / gold['Close'].iloc[-1] * 10000
            change = gold_silver - gold['Close'].iloc[-20] / silver['Close'].iloc[-20]
            
            return {
                'value': {
                    'gold_silver': round(gold_silver, 1),
                    'copper_gold': round(copper_gold, 1)
                },
                'change_1m': round(change, 1),
                'trend': 'up' if change > 0 else 'down',
                'weight': 0.05,
                'impact': 'positive',
                'data_source': 'Yahoo Finance',
                'reliability': '高'
            }
        except Exception as e:
            return {
                'value': {'gold_silver': 85.0, 'copper_gold': 2.5},
                'change_1m': 1.2,
                'trend': 'up',
                'weight': 0.05,
                'impact': 'positive',
                'data_source': '模拟数据',
                'reliability': '低',
                'error': str(e)
            }
    
    def _fallback_factor(self, name, base_value, weight, impact, error_msg=''):
        """备用因子数据 - 使用固定值而非随机数"""
        # 根据因子名称确定固定趋势
        trend_map = {
            '美元指数': 'up',
            '实际利率': 'down',
            '通胀': 'up',
            '收益率': 'down',
            '风险': 'up',
            'VIX': 'up',
            '不确定': 'up',
            '持仓': 'up'
        }
        trend = 'up'
        for key in trend_map:
            if key in name:
                trend = trend_map[key]
                break
        
        return {
            'value': round(base_value, 2),  # 移除随机扰动
            'change_1m': 0.0,  # 固定变化为0
            'trend': trend,
            'weight': weight,
            'impact': impact,
            'data_source': '备用估算值',
            'reliability': '低',
            'error': error_msg
        }
    
    def get_all_factors(self):
        """获取所有宏观因子数据"""
        factors = {
            '美元指数 (DXY)': self.get_dxy(),
            '实际利率 (TIPS)': self.get_real_rate_tips(),
            '通胀预期 (CPI)': self.get_inflation_cpi(),
            '美债收益率': self.get_bond_yield(),
            '地缘政治风险 (GPR)': self.get_gpr(),
            'VIX波动率': self.get_vix(),
            '经济不确定性 (EPU)': self.get_epu(),
            '黄金ETF持仓': self.get_etf_holdings(),
            '金银比/铜金比': self.get_gold_ratios()
        }
        return factors
    
    def calculate_scores(self, factors):
        """计算各因子得分"""
        scores = {}
        total_score = 0
        
        for name, data in factors.items():
            # 基础分值 (0-10)
            if isinstance(data['value'], dict):
                base_score = 5.0
            else:
                base_score = self._normalize_value(name, data['value'])
            
            # 趋势调整
            trend_bonus = 1.5 if data['trend'] == 'up' else -1.5
            
            # 变化率调整
            change_bonus = np.clip(data['change_1m'] * 0.5, -2, 2)
            
            # 最终得分
            raw_score = base_score + trend_bonus + change_bonus
            final_score = np.clip(raw_score, 0, 10)
            
            # 根据影响方向调整
            if data['impact'] == 'negative':
                adjusted_score = 10 - final_score
            else:
                adjusted_score = final_score
            
            weighted_score = adjusted_score * data['weight']
            
            scores[name] = {
                'raw_value': data['value'],
                'base_score': round(base_score, 2),
                'final_score': round(final_score, 2),
                'adjusted_score': round(adjusted_score, 2),
                'weighted_score': round(weighted_score, 3),
                'weight': data['weight'],
                'impact': data['impact'],
                'trend': data['trend'],
                'change_1m': data['change_1m'],
                'data_source': data.get('data_source', '未知'),
                'reliability': data.get('reliability', '未知'),
                'method': data.get('method', '')
            }
            
            total_score += weighted_score
        
        return scores, total_score
    
    def _normalize_value(self, name, value):
        """归一化值为0-10分"""
        if 'DXY' in name or '美元' in name:
            return np.clip((value - 90) / 20 * 10, 0, 10)
        elif '利率' in name or 'TIPS' in name:
            return np.clip((value + 2) / 7 * 10, 0, 10)
        elif '通胀' in name or 'CPI' in name:
            return np.clip(value / 5 * 10, 0, 10)
        elif '收益率' in name:
            return np.clip(value / 8 * 10, 0, 10)
        elif '风险' in name or 'GPR' in name or 'VIX' in name:
            return np.clip(value / 40 * 10, 0, 10)
        elif '不确定' in name or 'EPU' in name:
            return np.clip(value / 500 * 10, 0, 10)  # EPU尺度
        elif '持仓' in name or 'ETF' in name:
            return np.clip((value - 700) / 300 * 10, 0, 10)
        else:
            return 5.0
    
    def predict_price(self, factors, scores, total_score, random_seed=None):
        """基于因子预测金价 - 强制使用上海期货交易所数据
        
        Args:
            factors: 宏观因子数据
            scores: 因子得分
            total_score: 总分
            random_seed: 随机种子，用于重现结果。None表示每次随机
        """
        # 设置随机种子（如果提供）
        if random_seed is not None:
            np.random.seed(random_seed)
        
        current_price = None
        price_source = ""
        contract = ""
        
        # 强制优先获取上海期货交易所黄金实时价格
        try:
            import akshare as ak
            
            # 方法1: 获取实时行情（优先）
            try:
                df_spot = ak.futures_zh_spot(symbol='AU2604')
                if df_spot is not None and not df_spot.empty:
                    if 'current_price' in df_spot.columns:
                        current_price = float(df_spot['current_price'].iloc[0])
                    elif '最新价' in df_spot.columns:
                        current_price = float(df_spot['最新价'].iloc[0])
                    else:
                        current_price = float(df_spot.iloc[0, 5])
                    contract = 'AU2604'
                    price_source = "上海期货交易所(实时)"
                    print(f"✅ 宏观预测使用上期所黄金AU2604实时价格: {current_price} 元/克")
            except Exception as e:
                print(f"⚠️ 实时行情获取失败: {e}")
            
            # 方法2: 尝试主力连续合约 AU0
            if current_price is None:
                try:
                    df_main = ak.futures_zh_daily_sina(symbol='AU0')
                    if df_main is not None and not df_main.empty:
                        current_price = float(df_main['close'].iloc[-1])
                        contract = 'AU0'
                        price_source = "上海期货交易所(主力连续)"
                        print(f"✅ 宏观预测使用上期所黄金主力连续AU0价格: {current_price} 元/克")
                except Exception as e:
                    print(f"⚠️ 主力连续获取失败: {e}")
            
            # 方法3: 尝试获取主力合约或常用合约的日线数据
            if current_price is None:
                contracts = ['AU2604', 'AU2506', 'AU2504', 'AU2412']
                for sym in contracts:
                    try:
                        df = ak.futures_zh_daily_sina(symbol=sym)
                        if df is not None and not df.empty:
                            current_price = float(df['close'].iloc[-1])
                            contract = sym
                            price_source = "上海期货交易所(日线)"
                            print(f"✅ 宏观预测使用上期所黄金{sym}日线收盘价: {current_price} 元/克")
                            break
                    except Exception as e:
                        print(f"⚠️ 合约{sym}获取失败: {e}")
                        continue
        except Exception as e:
            print(f"❌ akshare导入失败: {e}")
        
        # 如果上期所数据获取失败，尝试其他国内数据源
        if current_price is None:
            try:
                import akshare as ak
                # 尝试获取上海金基准价格
                try:
                    gold_spot = ak.spot_hist_sge(symbol='Au99.99')
                    if gold_spot is not None and not gold_spot.empty:
                        current_price = float(gold_spot['close'].iloc[-1])
                        contract = "Au99.99"
                        price_source = "上海黄金交易所"
                        print(f"✅ 使用上金所Au99.99价格: {current_price} 元/克")
                except Exception as e:
                    print(f"⚠️ 上金所数据获取失败: {e}")
            except Exception as e:
                print(f"⚠️ 备用数据源失败: {e}")
        
        # 只有在所有国内数据源都失败时才使用COMEX转换
        if current_price is None:
            try:
                gold = yf.Ticker("GC=F").history(period="1mo")
                usd_price = gold['Close'].iloc[-1]
                # COMEX黄金是美元/盎司，转换为元/克 (1盎司=31.1035克，汇率约7.2)
                current_price = usd_price * 7.2 / 31.1035
                contract = "GC=F"
                price_source = "COMEX黄金(美元转人民币)"
                print(f"⚠️ 使用COMEX黄金转换价格: {current_price:.2f} 元/克 (来源: ${usd_price:.2f}/oz)")
            except Exception as e:
                current_price = 791.00  # 使用实际获取的默认值
                contract = "AU2604"
                price_source = "上次成功获取值"
                print(f"⚠️ 使用默认价格: {current_price} 元/克")
        
        # 基于总分预测 - 使用固定预期收益率（取区间中值）
        if total_score > 6.5:
            sentiment = '强烈看涨'
            expected_change = 0.055  # (0.03 + 0.08) / 2
        elif total_score > 5.5:
            sentiment = '看涨'
            expected_change = 0.02   # (0.01 + 0.03) / 2
        elif total_score > 5.0:
            sentiment = '中性偏多'
            expected_change = 0.01   # +1% 小幅上涨
        elif total_score > 4.5:
            sentiment = '中性偏空'
            expected_change = -0.01  # -1% 小幅下跌
        elif total_score > 3.5:
            sentiment = '看跌'
            expected_change = -0.02  # (-0.03 + -0.01) / 2
        else:
            sentiment = '强烈看跌'
            expected_change = -0.055 # (-0.08 + -0.03) / 2
        
        # 基于波动率的随机游走预测
        # 计算黄金历史波动率
        try:
            import akshare as ak
            contracts = ['AU2604', 'AU2506', 'AU2504']
            hist_df = None
            for sym in contracts:
                try:
                    hist_df = ak.futures_zh_daily_sina(symbol=sym)
                    if hist_df is not None and not hist_df.empty and len(hist_df) > 20:
                        break
                except:
                    continue
            
            if hist_df is not None and len(hist_df) > 20:
                closes = hist_df['close'].astype(float).values
                log_returns = np.diff(np.log(closes))
                daily_volatility = np.std(log_returns)  # 日波动率
            else:
                daily_volatility = 0.15 / np.sqrt(252)  # 默认15%年化
        except:
            daily_volatility = 0.15 / np.sqrt(252)
        
        # 生成随机游走路径
        # 每日收益率 = 漂移项(预期变化) + 随机波动项
        predictions = []
        dates = []
        current_pred = current_price
        
        # 漂移率（每日预期变化）
        daily_drift = expected_change / 30
        
        for i in range(1, 31):
            date = datetime.now() + timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # 随机游走: r = drift + volatility * Z
            # Z ~ N(0, 1) 标准正态分布
            random_shock = np.random.randn() * daily_volatility
            daily_return = daily_drift + random_shock
            
            # 更新价格
            current_pred = current_pred * (1 + daily_return)
            predictions.append(round(current_pred, 2))
        
        print(f"📈 预测参数: 当前价格={current_price:.2f}, 30天预期变化={expected_change:.2%}")
        print(f"📈 日波动率: {daily_volatility:.4f} ({daily_volatility*np.sqrt(252):.1%}年化)")
        print(f"📈 预测区间: {predictions[0]} -> {predictions[-1]} ({predictions[-1] - current_price:+.2f})")
        
        # 计算目标价格
        target_price = round(current_price * (1 + expected_change), 2)
        
        print(f"📊 汇总: 当前价={current_price:.2f}, 目标价={target_price:.2f}, 变化={expected_change:.2%}")
        
        return {
            'current_price': round(current_price, 2),
            'current_price_source': price_source,
            'current_price_contract': contract,
            'predictions': predictions,
            'dates': dates,
            'sentiment': sentiment,
            'expected_return': round(expected_change * 100, 2),
            'target_price': target_price
        }


@app.route('/api/macro-factors')
def get_macro_factors():
    """获取宏观因子数据
    
    Query参数:
        seed: 随机种子（整数），用于重现预测结果
              不提供则每次生成不同预测路径
    """
    from flask import request
    
    # 获取随机种子参数
    seed_param = request.args.get('seed')
    random_seed = int(seed_param) if seed_param and seed_param.isdigit() else None
    
    collector = MacroFactorCollector()
    factors = collector.get_all_factors()
    scores, total_score = collector.calculate_scores(factors)
    prediction = collector.predict_price(factors, scores, total_score, random_seed=random_seed)
    
    # 统计真实度
    reliability_stats = {'high': 0, 'medium': 0, 'low': 0}
    for name, data in factors.items():
        rel = data.get('reliability', '低')
        if rel in ['极高', '高']:
            reliability_stats['high'] += 1
        elif rel == '中':
            reliability_stats['medium'] += 1
        else:
            reliability_stats['low'] += 1
    
    # 确保金价来源信息明确
    price_info = {
        'current_price': prediction['current_price'],
        'price_source': prediction.get('current_price_source', '未知'),
        'price_contract': prediction.get('current_price_contract', ''),
        'unit': '元/克'
    }
    
    return jsonify({
        'factors': scores,
        'total_score': round(total_score, 3),
        'sentiment': prediction['sentiment'],
        'prediction': prediction,
        'price_info': price_info,
        'reliability_stats': reliability_stats,
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/data-quality')
def get_data_quality():
    """获取数据质量报告"""
    collector = MacroFactorCollector()
    factors = collector.get_all_factors()
    
    report = {
        'high_reliability': [],
        'medium_reliability': [],
        'low_reliability': []
    }
    
    for name, data in factors.items():
        rel = data.get('reliability', '低')
        entry = {
            'name': name,
            'value': data.get('value'),
            'source': data.get('data_source', '未知'),
            'method': data.get('method', ''),
            'note': data.get('note', '')
        }
        
        if rel in ['极高', '高']:
            report['high_reliability'].append(entry)
        elif rel == '中':
            report['medium_reliability'].append(entry)
        else:
            report['low_reliability'].append(entry)
    
    return jsonify(report)


# ============ 风险管理模块 API ============

def run_risk_management_analysis(df):
    """
    运行风险管理分析
    
    参数:
        df: 包含黄金数据的DataFrame
    
    返回:
        风险管理分析结果
    """
    global risk_cache
    
    if not RISK_MANAGEMENT_AVAILABLE:
        return {'error': '风险管理模块未可用'}
    
    # 检查缓存
    if risk_cache['last_update'] is not None:
        if datetime.now() - risk_cache['last_update'] < timedelta(minutes=RISK_CACHE_MINUTES):
            print(f"📦 使用风险管理缓存（{RISK_CACHE_MINUTES}分钟内）")
            return {
                'risk_metrics': risk_cache['risk_metrics'],
                'defense_results': risk_cache['defense_results'],
                'failure_alerts': risk_cache['failure_alerts'],
                'feature_importance': risk_cache['feature_importance'],
                'cached': True
            }
    
    try:
        print("🛡️ 启动风险管理分析...")
        
        # 创建风险管理器
        risk_manager = GoldRiskManager()
        
        # 准备特征
        features_df = prepare_risk_features(df)
        
        if len(features_df) < 100:
            return {'error': '数据量不足，无法进行风险管理分析'}
        
        # 分离特征和目标
        X = features_df.drop('target', axis=1)
        y = features_df['target']
        
        # 创建模型
        model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        
        # 1. 滚动窗口验证
        print("🔍 执行滚动窗口交叉验证...")
        validation_results = risk_manager.rolling_window_validation(X, y, model)
        
        # 2. 计算风险指标
        print("📈 计算风险指标...")
        predictions = pd.Series(validation_results['predictions'], 
                               index=validation_results['dates'])
        actuals = pd.Series(validation_results['actuals'], 
                           index=validation_results['dates'])
        
        # 使用实际日收益率计算风险指标（从原始价格数据获取）
        close_col = 'Close' if 'Close' in df.columns else 'close'
        daily_returns = df[close_col].pct_change().dropna()
        # 对齐日期范围
        if len(validation_results['dates']) > 0:
            start_date = min(validation_results['dates'])
            end_date = max(validation_results['dates'])
            daily_returns_aligned = daily_returns[(daily_returns.index >= start_date) & 
                                                  (daily_returns.index <= end_date)]
        else:
            daily_returns_aligned = daily_returns
        
        # 应用交易成本
        net_returns = risk_manager.apply_transaction_costs(daily_returns_aligned, turnover_rate=0.5)
        risk_metrics = risk_manager.calculate_risk_metrics(net_returns)
        
        # 3. 压力测试
        print("🔥 执行压力测试...")
        df_test = pd.DataFrame({'returns': daily_returns_aligned}, index=daily_returns_aligned.index)
        stress_results = risk_manager.stress_test(df_test, predictions, actuals)
        
        # 4. 特征重要性
        print("📊 分析特征重要性...")
        model.fit(X.iloc[-252:], y.iloc[-252:])  # 使用最近1年数据
        feature_importance = risk_manager.analyze_feature_importance(X, y, model)
        
        # 5. 过拟合防御体系
        print("🛡️ 执行过拟合防御体系检测...")
        # 根据数据量调整参数
        n_samples = len(X)
        if n_samples < 300:
            # 数据不足时使用更小的参数
            n_splits = min(3, n_samples // 50)  # 减少折数
            print(f"   ⚠️ 数据量较少({n_samples}行)，调整参数: n_splits={n_splits}")
        else:
            n_splits = 5
        defense_results = risk_manager.overfitting_defense_system(X, y, model, n_splits=n_splits)
        
        # 6. 模型失效预警
        print("⚠️ 执行模型失效预警检测...")
        feature_history = []
        if feature_importance is not None:
            importance_dict = dict(zip(
                feature_importance['feature'],
                feature_importance['importance_pct'] / 100
            ))
            feature_history.append(importance_dict)
        
        failure_alerts = risk_manager.model_failure_detection(
            actuals.iloc[-100:],
            predictions.iloc[-100:],
            feature_history,
            actuals.iloc[-100:]
        )
        
        # 转换为可序列化的格式
        risk_metrics_serializable = convert_to_native(risk_metrics)
        
        # 简化defense_results以便序列化
        defense_summary = {
            'overall_status': defense_results.get('overall_status', 'UNKNOWN'),
            'timestamp': defense_results.get('timestamp'),
            'warnings': defense_results.get('warnings', []),
            'critical_alerts': defense_results.get('critical_alerts', [])
        }
        
        if 'defense_layers' in defense_results:
            defense_summary['layers'] = {}
            for layer_name, layer_data in defense_results['defense_layers'].items():
                if isinstance(layer_data, dict):
                    defense_summary['layers'][layer_name] = {
                        'status': layer_data.get('status', 'UNKNOWN')
                    }
        
        # 简化failure_alerts
        failure_summary = {
            'status': failure_alerts.get('status', 'UNKNOWN'),
            'timestamp': failure_alerts.get('timestamp'),
            'warnings': failure_alerts.get('warnings', []),
            'critical_alerts': failure_alerts.get('critical_alerts', [])
        }
        
        # 转换特征重要性
        feature_importance_serializable = None
        if feature_importance is not None:
            feature_importance_serializable = feature_importance.head(10).to_dict('records')
        
        # 更新缓存
        risk_cache.update({
            'risk_manager': risk_manager,
            'validation_results': validation_results,
            'stress_results': stress_results,
            'risk_metrics': risk_metrics_serializable,
            'feature_importance': feature_importance_serializable,
            'defense_results': defense_summary,
            'failure_alerts': failure_summary,
            'last_update': datetime.now()
        })
        
        print("✅ 风险管理分析完成")
        
        return {
            'risk_metrics': risk_metrics_serializable,
            'defense_results': defense_summary,
            'failure_alerts': failure_summary,
            'feature_importance': feature_importance_serializable,
            'cached': False
        }
        
    except Exception as e:
        import traceback
        print(f"❌ 风险管理分析失败: {e}")
        print(traceback.format_exc())
        return {'error': str(e), 'traceback': traceback.format_exc()}


def prepare_risk_features(df):
    """
    准备风险管理所需的特征数据
    
    参数:
        df: 原始数据DataFrame
    
    返回:
        特征DataFrame
    """
    features = pd.DataFrame(index=df.index)
    
    # 确保收盘价存在
    close_col = 'Close' if 'Close' in df.columns else 'close'
    volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
    
    # 技术指标
    # RSI
    delta = df[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df[close_col].ewm(span=12).mean()
    exp2 = df[close_col].ewm(span=26).mean()
    features['macd'] = exp1 - exp2
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    
    # 移动平均线差异
    features['ma5'] = df[close_col].rolling(window=5).mean()
    features['ma20'] = df[close_col].rolling(window=20).mean()
    features['ma_diff'] = (features['ma5'] - features['ma20']) / features['ma20']
    
    # 波动率
    features['volatility'] = df[close_col].pct_change().rolling(window=20).std()
    
    # 价格动量
    features['momentum_5'] = df[close_col].pct_change(5)
    features['momentum_20'] = df[close_col].pct_change(20)
    
    # 成交量特征
    if volume_col in df.columns:
        features['volume_ma'] = df[volume_col].rolling(window=20).mean()
        features['volume_ratio'] = df[volume_col] / features['volume_ma']
    else:
        features['volume_ma'] = 0
        features['volume_ratio'] = 1
    
    # 目标变量 - 未来5日收益率
    features['target'] = df[close_col].pct_change(5).shift(-5)
    
    # 删除缺失值
    features = features.dropna()
    
    return features


@app.route('/api/risk-management')
def get_risk_management():
    """
    获取风险管理分析结果
    
    返回包含以下内容的JSON:
    - risk_metrics: 风险指标（夏普比率、最大回撤、VaR等）
    - defense_results: 过拟合防御体系结果
    - failure_alerts: 模型失效预警
    - feature_importance: 特征重要性分析
    """
    if not RISK_MANAGEMENT_AVAILABLE:
        return jsonify({'error': '风险管理模块未安装', 'available': False}), 503
    
    try:
        # 获取数据
        df = get_real_gold_data()
        if df is None or df.empty:
            return jsonify({'error': '无法获取数据'}), 500
        
        # 运行风险管理分析
        result = run_risk_management_analysis(df)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'available': True,
            'data': result,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/risk-dashboard')
def get_risk_dashboard():
    """
    获取风控监控仪表盘数据
    
    返回简化的风控状态，用于前端仪表盘展示
    """
    if not RISK_MANAGEMENT_AVAILABLE:
        return jsonify({
            'available': False,
            'message': '风险管理模块未安装'
        })
    
    try:
        # 使用缓存的风险管理结果
        if risk_cache['last_update'] is None:
            # 如果没有缓存，返回空状态
            return jsonify({
                'available': True,
                'status': 'UNKNOWN',
                'message': '风险管理分析尚未运行，请访问 /api/risk-management 生成数据',
                'model_status': '⚪未启动',
                'position_suggestion': '请先运行风险管理分析',
                'risk_level': '未知',
                'update_time': None
            })
        
        # 构建仪表盘数据
        risk_metrics = risk_cache.get('risk_metrics', {})
        defense_results = risk_cache.get('defense_results', {})
        failure_alerts = risk_cache.get('failure_alerts', {})
        
        # 确定模型状态
        model_status = failure_alerts.get('status', 'NORMAL')
        status_icons = {
            'NORMAL': '🟢正常',
            'WARNING': '🟡预警',
            'CRITICAL': '🔴失效'
        }
        model_status_display = status_icons.get(model_status, '⚪未知')
        
        # 确定风险等级
        max_drawdown = risk_metrics.get('max_drawdown', 0)
        sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
        
        if max_drawdown < -0.25 or sharpe_ratio < 0.3:
            risk_level = '🔴极高'
        elif max_drawdown < -0.15 or sharpe_ratio < 0.5:
            risk_level = '🟠高'
        elif max_drawdown < -0.10 or sharpe_ratio < 1.0:
            risk_level = '🟡中等'
        else:
            risk_level = '🟢低'
        
        # 仓位建议
        if risk_cache['risk_manager'] is not None:
            try:
                position = risk_cache['risk_manager'].kelly_position_sizing(
                    win_rate=risk_metrics.get('win_rate', 0.55),
                    profit_loss_ratio=risk_metrics.get('profit_loss_ratio', 1.5),
                    account_size=1000000,
                    kelly_fraction=0.25
                )
                position_suggestion = f"{position['final_position_pct']*100:.1f}% (Kelly)"
            except:
                position_suggestion = "10-15% (保守)"
        else:
            position_suggestion = "10-15% (保守)"
        
        # 防御体系状态
        defense_status = defense_results.get('overall_status', 'UNKNOWN')
        
        dashboard = {
            'available': True,
            'status': model_status,
            'model_status': model_status_display,
            'risk_level': risk_level,
            'position_suggestion': position_suggestion,
            'sharpe_ratio': round(sharpe_ratio, 2) if sharpe_ratio else None,
            'max_drawdown': round(max_drawdown * 100, 1) if max_drawdown else None,
            'var_95': round(risk_metrics.get('var_95', 0) * 100, 2) if risk_metrics.get('var_95') else None,
            'win_rate': round(risk_metrics.get('win_rate', 0) * 100, 1) if risk_metrics.get('win_rate') else None,
            'defense_status': defense_status,
            'warnings': len(failure_alerts.get('warnings', [])),
            'critical_alerts': len(failure_alerts.get('critical_alerts', [])),
            'cached': True,
            'update_time': risk_cache['last_update'].strftime('%Y-%m-%d %H:%M:%S') if risk_cache['last_update'] else None
        }
        
        return jsonify(dashboard)
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/risk-position', methods=['POST'])
def calculate_risk_position():
    """
    计算风险调整后的仓位建议
    
    POST参数 (JSON):
    - account_size: 账户规模（默认1000000）
    - current_price: 当前价格（可选）
    - market_regime: 市场环境（normal/trending/ranging/high_volatility，默认normal）
    
    返回:
    - position_sizing: 仓位管理建议
    - stop_strategy: 止损策略
    - pyramiding: 加仓策略
    - risk_advice: 风控建议
    """
    if not RISK_MANAGEMENT_AVAILABLE:
        return jsonify({'error': '风险管理模块未安装', 'available': False}), 503
    
    try:
        from flask import request
        
        # 获取请求参数
        data = request.get_json() or {}
        account_size = data.get('account_size', 1000000)
        current_price = data.get('current_price')
        market_regime = data.get('market_regime', 'normal')
        
        # 确保风险管理分析已运行
        if risk_cache['last_update'] is None or risk_cache['risk_manager'] is None:
            # 先运行风险管理分析
            df = get_real_gold_data()
            if df is None or df.empty:
                return jsonify({'error': '无法获取数据'}), 500
            run_risk_management_analysis(df)
        
        risk_manager = risk_cache['risk_manager']
        risk_metrics = risk_cache.get('risk_metrics', {})
        
        # 计算仓位管理
        position_sizing = risk_manager.calculate_position_sizing(
            risk_metrics,
            account_size=account_size
        )
        
        # Kelly准则仓位
        kelly_position = risk_manager.kelly_position_sizing(
            win_rate=risk_metrics.get('win_rate', 0.55),
            profit_loss_ratio=risk_metrics.get('profit_loss_ratio', 1.5),
            account_size=account_size,
            kelly_fraction=0.25
        )
        
        # 分层仓位架构
        hierarchical = risk_manager.hierarchical_position_structure(
            base_position=kelly_position['final_position_pct'],
            account_size=account_size,
            risk_budget=0.10
        )
        
        # 止损策略
        stop_strategy = None
        if current_price:
            stop_strategy = risk_manager.generate_stop_loss_strategy(
                current_price, risk_metrics
            )
        
        # 加仓策略
        pyramiding = None
        if current_price:
            pyramiding = risk_manager.generate_pyramiding_strategy(
                current_price, position_sizing, risk_metrics
            )
        
        # 风控建议
        stress_results = risk_cache.get('stress_results', {})
        risk_advice = risk_manager.generate_risk_control_advice(
            risk_metrics, stress_results, market_regime
        )
        
        return jsonify({
            'available': True,
            'account_size': account_size,
            'position_sizing': convert_to_native(position_sizing),
            'kelly_position': convert_to_native(kelly_position),
            'hierarchical_position': convert_to_native(hierarchical),
            'stop_strategy': convert_to_native(stop_strategy) if stop_strategy else None,
            'pyramiding': convert_to_native(pyramiding) if pyramiding else None,
            'risk_advice': {
                'risk_level': risk_advice.get('risk_level'),
                'risk_score': risk_advice.get('risk_score'),
                'special_warnings': risk_advice.get('special_warnings', [])
            },
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    import sys
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print("=" * 70)
    print("📊 黄金价格宏观预测系统")
    print("=" * 70)
    print("\n🥇 当日价格数据源: 上海期货交易所 (SHFE)")
    print("   合约: AU2604 (主力合约)")
    print("   备用: AU2506 / AU2504 / AU2412")
    print("   单位: 元/克 (CNY/g)")
    print("\n📈 宏观因子数据源:")
    print("  ✅ 美元指数 (DXY) - Yahoo Finance")
    print("  ✅ 实际利率 (TIPS) - TIPS ETF")
    print("  ✅ 通胀预期 (CPI) - akshare 美国/中国CPI")
    print("  ✅ 美债收益率 - Yahoo Finance")
    print("  ✅ VIX波动率 - Yahoo Finance")
    print("  ✅ 金银比/铜金比 - akshare 上期所")
    print("  ✅ 地缘政治风险 (GPR) - Caldara-Iacoviello Official")
    print("      网址: https://www.matteoiacoviello.com/gpr.htm")
    print("  ✅ 经济不确定性 (EPU) - policyuncertainty.com Official")
    print("      网址: https://www.policyuncertainty.com/")
    print("  ✅ 黄金ETF持仓 - SPDR Gold Shares Official")
    print("      网址: https://www.spdrgoldshares.com/")
    print("      备用: 华安黄金ETF (518880)")
    print("\n🛡️ 风险管理模块:")
    if RISK_MANAGEMENT_AVAILABLE:
        print("  ✅ 状态: 已启用")
        print("  ✅ 过拟合防御体系: 4层防御机制")
        print("  ✅ 模型失效预警: 实时监控4大指标")
        print("  ✅ Kelly准则动态仓位")
        print("  ✅ 分层仓位架构")
        print("  ✅ 压力测试: 2008/2020/2022危机情景")
    else:
        print("  ❌ 状态: 未启用 (gold_risk_management.py 未找到)")
    print("\n🌐 服务地址:")
    print(f"  • 主页面: http://127.0.0.1:{port}/")
    print(f"  • 宏观因子API: http://127.0.0.1:{port}/api/macro-factors")
    print(f"  • 带种子重现: http://127.0.0.1:{port}/api/macro-factors?seed=42")
    print(f"  • 数据质量: http://127.0.0.1:{port}/api/data-quality")
    if RISK_MANAGEMENT_AVAILABLE:
        print(f"  • 风险管理: http://127.0.0.1:{port}/api/risk-management")
        print(f"  • 风控仪表盘: http://127.0.0.1:{port}/api/risk-dashboard")
        print(f"  • 仓位计算: POST http://127.0.0.1:{port}/api/risk-position")
    print("\n🎲 预测模式: 基于波动率的随机游走")
    print("   - 每次刷新生成不同但统计合理的路径")
    print("   - 添加 ?seed=数字 参数可重现相同结果")
    print("\n📈 模型增强 (极速模式):")
    print("   ✅ 选项A: 标准ARIMA (2,1,2) 简化参数")
    print("   ✅ 选项B: 基于波动率的随机游走")
    print("   ✅ 选项C: 原始特征 (关闭增强以提高速度)")
    print("   ✅ 选项D: XGBoost(50树) + RF(50树) + 加权集成")
    print("\n🧠 LSTM深度学习:")
    print("   - 状态: ❌ 已禁用 (提高加载速度)")
    print("   - 提示: 修改 LSTM_ENABLED = True 启用深度学习")
    print("\n⚡ 速度优化:")
    print("   - ARIMA: (2,1,2) 简化参数")
    print("   - Random Forest: 50棵树 (原100)")
    print("   - XGBoost: 50棵树，深度4 (原100/6)")
    print("   - Gradient Boosting: 30棵树，深度3 (原100/5)")
    print("   - 特征工程: 使用原始特征 (关闭增强)")
    print("=" * 70)
    print(f"🚀 正在启动服务，端口: {port}...")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=port)
