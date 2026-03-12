"""
铜价预测脚本 - 使用上海期货交易所铜期货数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

def get_copper_data():
    """获取铜期货数据"""
    try:
        import akshare as ak
        
        # 尝试获取上海期货交易所铜期货数据
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
                    
                    print(f"✅ 成功获取铜期货 {contract} 数据: {len(df)} 条")
                    print(f"   最新收盘价: {df['Close'].iloc[-1]:.2f} 元/吨")
                    return df
            except Exception as e:
                print(f"  合约{contract}获取失败: {e}")
                continue
        
        # 备用：使用yfinance获取COMEX铜
        import yfinance as yf
        copper = yf.Ticker("HG=F")
        df = copper.history(period="1y")
        if not df.empty:
            df.attrs['data_source'] = "COMEX铜期货 (HG=F)"
            print(f"✅ 成功获取COMEX铜期货数据: {len(df)} 条")
            print(f"   最新收盘价: ${df['Close'].iloc[-1]:.2f}/磅")
            return df
            
    except Exception as e:
        print(f"❌ 铜价数据获取失败: {e}")
        return None

def calculate_indicators(df):
    """计算技术指标"""
    # 移动平均线
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    
    # 波动率
    df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
    
    return df

def predict_copper():
    """铜价预测主函数"""
    print("="*60)
    print("🔶 铜价预测系统")
    print("="*60)
    
    # 获取数据
    df = get_copper_data()
    if df is None or df.empty:
        print("❌ 无法获取铜价数据")
        return
    
    # 计算技术指标
    df = calculate_indicators(df)
    df = df.dropna()
    
    # 准备特征
    df['Returns'] = df['Close'].pct_change()
    df['Target'] = df['Close'].shift(-1)  # 预测下一日价格
    df = df.dropna()
    
    # 特征工程
    features = ['Close', 'MA5', 'MA20', 'RSI', 'MACD', 'Volatility']
    X = df[features]
    y = df['Target']
    
    # 划分训练集和测试集（最后30天作为测试）
    train_size = len(X) - 30
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
    
    # 训练模型
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=50, random_state=42)
    }
    
    predictions = {}
    current_price = df['Close'].iloc[-1]
    
    print(f"\n📊 当前铜价: {current_price:.2f}")
    print("-"*60)
    
    for name, model in models.items():
        # 训练
        model.fit(X_train, y_train)
        
        # 预测未来7天
        future_preds = []
        last_row = X.iloc[-1:].copy()
        
        for i in range(7):
            pred = model.predict(last_row)[0]
            future_preds.append(pred)
            # 更新特征用于下一步预测（简化处理）
            last_row['Close'] = pred
        
        predictions[name] = future_preds
        
        # 计算预测涨跌
        change = (future_preds[-1] - current_price) / current_price * 100
        direction = "📈" if change > 0 else "📉"
        print(f"{name:20s}: 7日后预测 {future_preds[-1]:.2f} ({direction} {change:+.2f}%)")
    
    # 集成预测（简单平均）
    ensemble_preds = []
    for i in range(7):
        avg = np.mean([predictions[m][i] for m in predictions])
        ensemble_preds.append(avg)
    
    ensemble_change = (ensemble_preds[-1] - current_price) / current_price * 100
    ensemble_direction = "📈" if ensemble_change > 0 else "📉"
    
    print("-"*60)
    print(f"{'集成预测':20s}: 7日后预测 {ensemble_preds[-1]:.2f} ({ensemble_direction} {ensemble_change:+.2f}%)")
    
    # 未来7天预测详情
    print("\n📅 未来7天预测详情:")
    dates = [(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]
    for i, (date, price) in enumerate(zip(dates, ensemble_preds)):
        change = (price - current_price) / current_price * 100
        print(f"  {date}: {price:.2f} ({change:+.2f}%)")
    
    print("="*60)

if __name__ == "__main__":
    predict_copper()
