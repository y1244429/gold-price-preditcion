"""
黄金价格数据加载模块
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


class GoldDataLoader:
    """黄金价格数据加载器"""
    
    def __init__(self, symbol="GC=F", start_date="2020-01-01", end_date=None):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    
    def fetch_data(self):
        """从Yahoo Finance获取黄金数据"""
        print(f"正在下载 {self.symbol} 数据...")
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(start=self.start_date, end=self.end_date)
            
            if df.empty:
                print("警告: 无法获取数据，将使用模拟数据")
                return self._generate_mock_data()
            
            df = df.reset_index()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            elif 'Datetime' in df.columns:
                df['Date'] = pd.to_datetime(df['Datetime'])
            
            print(f"成功获取 {len(df)} 条数据")
            return df
        except Exception as e:
            print(f"获取数据失败: {e}")
            print("将使用模拟数据")
            return self._generate_mock_data()
    
    def _generate_mock_data(self):
        """生成模拟黄金数据用于测试"""
        print("生成模拟黄金数据...")
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        np.random.seed(42)
        
        # 生成具有趋势和波动的模拟价格
        base_price = 1800
        trend = np.linspace(0, 200, len(dates))
        volatility = np.cumsum(np.random.randn(len(dates)) * 15)
        prices = base_price + trend + volatility
        
        df = pd.DataFrame({
            'Date': dates,
            'Open': prices + np.random.randn(len(dates)) * 5,
            'High': prices + np.abs(np.random.randn(len(dates))) * 10 + 5,
            'Low': prices - np.abs(np.random.randn(len(dates))) * 10 - 5,
            'Close': prices + np.random.randn(len(dates)) * 3,
            'Volume': np.random.randint(100000, 500000, len(dates))
        })
        
        print(f"生成 {len(df)} 条模拟数据")
        return df
    
    def add_technical_indicators(self, df):
        """添加技术指标"""
        df = df.copy()
        
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 指数移动平均线
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # 价格波动
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_Abs'] = df['Price_Change'].abs()
        
        # 成交量移动平均
        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        
        return df
