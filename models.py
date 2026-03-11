"""
黄金价格预测模型
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

# 尝试导入TensorFlow，如果不存在则设置标志
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    # 延迟警告到实际使用LSTM时


class BaseModel:
    """基础模型类"""
    
    def __init__(self, name):
        self.name = name
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_trained = False
    
    def prepare_data(self, df, lookback_window=60):
        """准备时间序列数据"""
        data = df['Close'].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(lookback_window, len(scaled_data)):
            X.append(scaled_data[i-lookback_window:i, 0])
            y.append(scaled_data[i, 0])
        
        X, y = np.array(X), np.array(y)
        return X, y
    
    def evaluate(self, y_true, y_pred):
        """评估模型性能"""
        y_true_inv = self.scaler.inverse_transform(y_true.reshape(-1, 1)).flatten()
        y_pred_inv = self.scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
        
        mse = mean_squared_error(y_true_inv, y_pred_inv)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true_inv, y_pred_inv)
        r2 = r2_score(y_true_inv, y_pred_inv)
        mape = np.mean(np.abs((y_true_inv - y_pred_inv) / y_true_inv)) * 100
        
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'MAPE': mape
        }


class LSTMModel(BaseModel):
    """LSTM深度学习模型"""
    
    def __init__(self, lookback_window=60, units=50):
        super().__init__("LSTM")
        self.lookback_window = lookback_window
        self.units = units
    
    def build_model(self):
        """构建LSTM模型"""
        model = Sequential([
            LSTM(units=self.units, return_sequences=True, 
                 input_shape=(self.lookback_window, 1)),
            Dropout(0.2),
            LSTM(units=self.units, return_sequences=True),
            Dropout(0.2),
            LSTM(units=self.units),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        self.model = model
        return model
    
    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.1):
        """训练模型"""
        if self.model is None:
            self.build_model()
        
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        
        early_stop = EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=1
        )
        
        self.is_trained = True
        return history
    
    def predict(self, X):
        """预测"""
        X = X.reshape((X.shape[0], X.shape[1], 1))
        return self.model.predict(X, verbose=0)
    
    def forecast_future(self, last_sequence, days=7):
        """预测未来多天"""
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(days):
            X_pred = current_sequence.reshape((1, self.lookback_window, 1))
            pred = self.model.predict(X_pred, verbose=0)[0, 0]
            predictions.append(pred)
            
            # 滑动窗口更新
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = pred
        
        predictions = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(predictions).flatten()


class RandomForestModel(BaseModel):
    """随机森林模型"""
    
    def __init__(self, n_estimators=100, max_depth=10):
        super().__init__("Random Forest")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
    
    def build_model(self):
        """构建随机森林模型"""
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=42,
            n_jobs=-1
        )
        return self.model
    
    def train(self, X_train, y_train):
        """训练模型"""
        if self.model is None:
            self.build_model()
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        return self
    
    def predict(self, X):
        """预测"""
        return self.model.predict(X).reshape(-1, 1)
    
    def forecast_future(self, last_sequence, days=7):
        """预测未来多天"""
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(days):
            pred = self.model.predict(current_sequence.reshape(1, -1))[0]
            predictions.append(pred)
            
            # 滑动窗口更新
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = pred
        
        predictions = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(predictions).flatten()
    
    def feature_importance(self):
        """获取特征重要性"""
        if self.model is None or not self.is_trained:
            return None
        return self.model.feature_importances_


class ARIMAModel(BaseModel):
    """ARIMA时间序列模型"""
    
    def __init__(self, order=(5, 1, 0)):
        super().__init__("ARIMA")
        self.order = order
    
    def prepare_data(self, df, lookback_window=60):
        """准备ARIMA数据（不需要滑动窗口）"""
        data = df['Close'].values
        return data, None
    
    def train(self, data):
        """训练ARIMA模型"""
        self.model = ARIMA(data, order=self.order)
        self.fitted_model = self.model.fit()
        self.is_trained = True
        self.data = data
        return self
    
    def predict(self, start, end):
        """预测"""
        return self.fitted_model.predict(start=start, end=end)
    
    def forecast_future(self, days=7):
        """预测未来多天"""
        forecast = self.fitted_model.forecast(steps=days)
        return forecast
    
    def summary(self):
        """模型摘要"""
        if self.fitted_model is not None:
            return self.fitted_model.summary()
        return None


class LinearRegressionModel(BaseModel):
    """线性回归模型"""
    
    def __init__(self):
        super().__init__("Linear Regression")
    
    def build_model(self):
        """构建线性回归模型"""
        self.model = LinearRegression()
        return self.model
    
    def train(self, X_train, y_train):
        """训练模型"""
        if self.model is None:
            self.build_model()
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        return self
    
    def predict(self, X):
        """预测"""
        return self.model.predict(X).reshape(-1, 1)
    
    def forecast_future(self, last_sequence, days=7):
        """预测未来多天"""
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(days):
            pred = self.model.predict(current_sequence.reshape(1, -1))[0]
            predictions.append(pred)
            
            # 滑动窗口更新
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = pred
        
        predictions = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(predictions).flatten()
