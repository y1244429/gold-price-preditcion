import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from gold_app import get_real_gold_data, prepare_risk_features

# 获取数据
df = get_real_gold_data()
features_df = prepare_risk_features(df)
print(f'数据量: {len(features_df)} 行')

X = features_df.drop('target', axis=1)
y = features_df['target']

model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)

n_samples = len(X)
min_train_size = max(50, int(n_samples * 0.6))
step_size = max(5, int((n_samples - min_train_size) / 3))
print(f'训练窗口: {min_train_size}, 步长: {step_size}')

r2_scores = []
for start_idx in range(min_train_size, n_samples - step_size, step_size):
    end_idx = start_idx + step_size
    X_train, y_train = X.iloc[:start_idx], y.iloc[:start_idx]
    X_test, y_test = X.iloc[start_idx:end_idx], y.iloc[start_idx:end_idx]
    try:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        r2 = r2_score(y_test, pred)
        r2_scores.append(r2)
        print(f'  窗口 {len(r2_scores)}: R² = {r2:.4f}')
    except Exception as e:
        print(f'  失败: {e}')

print(f'\nR² 分数: {[f"{x:.2f}" for x in r2_scores]}')
print(f'平均 R²: {np.mean(r2_scores):.4f}')

# 检测连续低 R²
max_low_streak = 0
low_r2_streak = 0
for r2 in r2_scores:
    if r2 < 0.3:
        low_r2_streak += 1
        max_low_streak = max(max_low_streak, low_r2_streak)
    else:
        low_r2_streak = 0
print(f'最长连续低 R² (<0.3): {max_low_streak} 期')
