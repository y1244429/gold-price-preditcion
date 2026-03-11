# 黄金价格预测模型计算逻辑说明

## 📊 当前模型实现

### 1. Linear Regression (线性回归)

**算法**: scikit-learn `LinearRegression`

**特征工程**:
```python
lookback = 20  # 使用过去20天价格作为特征
X = [prices[i-20:i]]  # 输入: 过去20天价格序列
y = [prices[i]]        # 输出: 第21天价格
```

**未来7天预测逻辑**:
```python
lr_future = []
current_seq = prices[-20:].copy()  # 最近20天价格
for _ in range(7):
    pred = lr.predict(current_seq.reshape(1, -1))[0]  # 预测下一天
    lr_future.append(pred)
    current_seq = np.roll(current_seq, -1)  # 序列左移
    current_seq[-1] = pred  # 将预测值加入序列末尾
```

**特点**:
- 简单线性关系，容易过拟合
- 对趋势跟踪较好，对波动不敏感

---

### 2. Random Forest (随机森林)

**算法**: scikit-learn `RandomForestRegressor`

**参数**:
```python
n_estimators=50    # 50棵树
max_depth=10       # 最大深度10
random_state=42    # 固定随机种子
```

**特征工程**和预测逻辑与线性回归相同。

**特点**:
- 非线性关系，抗过拟合能力较强
- 能捕捉一些复杂的模式

---

### 3. ARIMA (自回归积分滑动平均)

**当前实现**: 简化版趋势预测（非标准ARIMA）

**计算逻辑**:
```python
arima_future = []
last_price = prices[-1]  # 最新价格
trend = np.mean(np.diff(prices[-10:]))  # 最近10天平均变化
for i in range(7):
    pred = last_price + trend * (i + 1)  # 线性外推
    arima_future.append(pred)
```

**特点**:
- 纯趋势跟踪
- 没有自回归和滑动平均组件

---

### 4. 集成预测 (Ensemble)

**当前实现**: 三模型简单平均

```python
ensemble = (lr_pred + rf_pred + arima_pred) / 3
```

---

## ❌ 当前问题

1. **所有模型都使用相同的特征**（过去20天价格），缺乏多样性
2. **ARIMA实现过于简化**，不是真正的ARIMA模型
3. **没有使用TensorFlow/深度学习**
4. **缺乏特征工程**：没有使用技术指标（RSI、MACD等）
5. **没有使用宏观因子数据**进行预测

---

## 🤔 关于 TensorFlow

**当前状态**: ❌ 没有使用TensorFlow

**可以添加的TensorFlow模型**:

### 1. LSTM (长短期记忆网络)
```python
import tensorflow as tf

model = tf.keras.Sequential([
    tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(20, 1)),
    tf.keras.layers.LSTM(50),
    tf.keras.layers.Dense(7)  # 预测未来7天
])
```

### 2. 添加宏观因子的神经网络
```python
# 价格序列输入
price_input = tf.keras.layers.Input(shape=(20, 1))
x = tf.keras.layers.LSTM(32)(price_input)

# 宏观因子输入
macro_input = tf.keras.layers.Input(shape=(9,))  # 9个宏观因子
y = tf.keras.layers.Dense(16, activation='relu')(macro_input)

# 合并
combined = tf.keras.layers.concatenate([x, y])
output = tf.keras.layers.Dense(7)(combined)

model = tf.keras.Model(inputs=[price_input, macro_input], outputs=output)
```

---

## 🎯 建议改进方案

### 方案 A: 修复ARIMA实现
使用标准的statsmodels ARIMA：
```python
from statsmodels.tsa.arima.model import ARIMA

model = ARIMA(prices, order=(5,1,0))
model_fit = model.fit()
forecast = model_fit.forecast(steps=7)
```

### 方案 B: 添加TensorFlow LSTM
添加深度学习模型提高预测精度。

### 方案 C: 特征工程增强
- 添加技术指标（RSI、MACD、布林带）
- 添加宏观因子作为特征
- 使用更多的时间序列特征

### 方案 D: 集成学习改进
- 使用加权平均（根据模型历史表现）
- 添加更多模型（XGBoost、LightGBM等）

---

您想要哪种改进？
