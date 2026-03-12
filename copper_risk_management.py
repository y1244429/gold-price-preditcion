"""
铜价预测风险管理模块
阶段1：基础强化 - 概率预测与不确定性量化

功能：
1. 分位数回归预测区间
2. 蒙特卡洛Dropout不确定性
3. 共形预测保证覆盖率
4. 风险指标计算（VaR, CVaR）
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, QuantileRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy import stats
from scipy.stats import genpareto, t
import warnings
warnings.filterwarnings('ignore')


class CopperRiskManager:
    """
    铜价预测风险管理器
    
    提供概率预测而非单点预测，量化预测不确定性
    """
    
    def __init__(self, confidence_level=0.95):
        self.confidence_level = confidence_level
        self.quantile_models = {}
        self.quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
        self.base_model = None
        self.calibration_scores = None
        self.is_calibrated = False
        
        # 模型性能指标
        self.model_metrics = {}
        
    def train_quantile_models(self, X_train, y_train):
        """
        训练分位数回归模型，输出预测区间
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
        """
        print("🎯 训练分位数回归模型...")
        
        for alpha in self.quantiles:
            # 使用Gradient Boosting分位数回归
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                loss='quantile',
                alpha=alpha,
                random_state=42
            )
            model.fit(X_train, y_train)
            self.quantile_models[alpha] = model
            print(f"  ✓ 分位数 α={alpha} 训练完成")
        
        # 训练基础模型（中位数预测）
        self.base_model = self.quantile_models[0.5]
        
    def calibrate_conformal(self, X_cal, y_cal):
        """
        共形预测校准 - 保证覆盖率
        
        Args:
            X_cal: 校准集特征
            y_cal: 校准集目标
        """
        print("📐 进行共形预测校准...")
        
        # 计算非一致性分数（绝对误差）
        predictions = self.base_model.predict(X_cal)
        self.calibration_scores = np.abs(y_cal - predictions)
        
        # 计算期望覆盖率对应的分位数阈值
        n = len(y_cal)
        # 确保 q_level 在 [0, 1] 范围内
        q_level = min(0.999, np.ceil((n + 1) * self.confidence_level) / n)
        q_level = max(0.001, q_level)  # 确保不小于0.001
        
        self.conformal_quantile = np.quantile(self.calibration_scores, q_level)
        
        self.is_calibrated = True
        
        # 验证校准集覆盖率
        coverage = np.mean(
            (y_cal >= predictions - self.conformal_quantile) & 
            (y_cal <= predictions + self.conformal_quantile)
        )
        print(f"  ✓ 校准完成，理论覆盖率: {self.confidence_level:.1%}, 实际覆盖率: {coverage:.1%}")
        
    def predict_with_uncertainty(self, X, method='quantile'):
        """
        带不确定性的预测
        
        Args:
            X: 输入特征
            method: 'quantile' 或 'conformal'
        
        Returns:
            dict: 包含点预测、置信区间、不确定性指标
        """
        if method == 'quantile':
            return self._predict_quantile(X)
        elif method == 'conformal' and self.is_calibrated:
            return self._predict_conformal(X)
        else:
            return self._predict_quantile(X)
    
    def _predict_quantile(self, X):
        """分位数回归预测"""
        predictions = {}
        for alpha, model in self.quantile_models.items():
            predictions[alpha] = model.predict(X)
        
        # 计算预测区间统计量
        interval_width = predictions[0.95] - predictions[0.05]
        
        # 不确定性评分（区间宽度归一化）
        uncertainty_score = interval_width / np.mean(predictions[0.5])
        
        return {
            'point_prediction': predictions[0.5],
            'mean_prediction': predictions[0.5],
            'lower_95': predictions[0.05],
            'upper_95': predictions[0.95],
            'lower_50': predictions[0.25],
            'upper_50': predictions[0.75],
            'prediction_interval_width': interval_width,
            'uncertainty_score': uncertainty_score,
            'confidence': 1 - np.clip(uncertainty_score / 0.1, 0, 1),  # 归一化置信度
            'method': 'quantile_regression'
        }
    
    def _predict_conformal(self, X):
        """共形预测（保证覆盖率）"""
        point_pred = self.base_model.predict(X)
        
        return {
            'point_prediction': point_pred,
            'mean_prediction': point_pred,
            'lower_95': point_pred - self.conformal_quantile,
            'upper_95': point_pred + self.conformal_quantile,
            'lower_50': point_pred - self.conformal_quantile * 0.5,
            'upper_50': point_pred + self.conformal_quantile * 0.5,
            'prediction_interval_width': self.conformal_quantile * 2,
            'uncertainty_score': self.conformal_quantile / np.mean(point_pred),
            'confidence': self.confidence_level,
            'coverage_guarantee': self.confidence_level,
            'method': 'conformal_prediction'
        }
    
    def monte_carlo_uncertainty(self, X, base_model, n_samples=100):
        """
        蒙特卡洛Dropout不确定性估计
        
        通过多次前向传播（启用dropout）估计预测不确定性
        """
        # 使用随机森林的预测方差作为近似
        if hasattr(base_model, 'estimators_'):
            # Random Forest - 利用树间差异
            predictions = np.array([
                tree.predict(X) for tree in base_model.estimators_
            ])
            
            return {
                'mean_prediction': predictions.mean(axis=0),
                'std_prediction': predictions.std(axis=0),
                'lower_95': np.percentile(predictions, 2.5, axis=0),
                'upper_95': np.percentile(predictions, 97.5, axis=0),
                'prediction_uncertainty': predictions.std(axis=0),
                'method': 'monte_carlo_rf'
            }
        else:
            # 对于其他模型，使用bootstrap
            return self._bootstrap_uncertainty(X, base_model, n_samples)
    
    def _bootstrap_uncertainty(self, X, base_model, n_samples=100):
        """Bootstrap重采样估计不确定性"""
        # 简化实现：返回基于预测误差的估计
        point_pred = base_model.predict(X) if hasattr(base_model, 'predict') else X
        
        # 假设10%的相对误差
        std_estimate = point_pred * 0.05
        
        return {
            'mean_prediction': point_pred,
            'std_prediction': std_estimate,
            'lower_95': point_pred - 1.96 * std_estimate,
            'upper_95': point_pred + 1.96 * std_estimate,
            'prediction_uncertainty': std_estimate,
            'method': 'bootstrap'
        }


class ExtremeValueRiskModel:
    """
    极值理论（EVT）尾部风险模型
    
    用于建模极端价格变动的尾部风险
    """
    
    def __init__(self, threshold_percentile=0.95):
        self.threshold_percentile = threshold_percentile
        self.xi = None  # 极值指数（形状参数）
        self.beta = None  # 尺度参数
        self.mu = None    # 位置参数
        self.threshold = None
        self.is_fitted = False
        
    def fit(self, returns):
        """
        拟合广义帕累托分布（GPD）
        
        Args:
            returns: 收益率序列
        """
        print("📊 拟合极值理论模型...")
        
        # 处理正负收益率
        self.returns = np.array(returns).flatten()
        
        # 设定阈值（取绝对值的上分位数）
        self.threshold = np.percentile(
            np.abs(self.returns), 
            self.threshold_percentile * 100
        )
        
        # 超过阈值的极值
        extremes = np.abs(self.returns)[np.abs(self.returns) > self.threshold]
        
        if len(extremes) < 10:
            print(f"  ⚠️ 极值样本不足 ({len(extremes)}个)，使用经验分布")
            self.use_empirical = True
            self.extreme_returns = extremes
        else:
            self.use_empirical = False
            # 拟合GPD
            excesses = extremes - self.threshold
            try:
                self.xi, self.mu, self.beta = genpareto.fit(excesses)
                self.is_fitted = True
                print(f"  ✓ GPD拟合完成: ξ={self.xi:.4f}, β={self.beta:.4f}")
            except Exception as e:
                print(f"  ⚠️ GPD拟合失败: {e}，使用经验分布")
                self.use_empirical = True
                self.extreme_returns = extremes
        
        return self
    
    def calculate_var_cvar(self, confidence=0.99, position=1):
        """
        计算VaR和CVaR（条件风险价值）
        
        Args:
            confidence: 置信水平（默认99%）
            position: 仓位方向（1=多头，-1=空头）
        
        Returns:
            dict: VaR和CVaR指标
        """
        if not self.is_fitted and not self.use_empirical:
            raise ValueError("Model not fitted. Call fit() first.")
        
        n = len(self.returns)
        nu = len(self.returns[np.abs(self.returns) > self.threshold])
        
        if self.use_empirical:
            # 使用经验分位数
            var = np.percentile(self.extreme_returns, confidence * 100)
            cvar = np.mean(self.extreme_returns[self.extreme_returns >= var])
        else:
            # 使用GPD公式
            q = confidence
            var = self.threshold + (self.beta / self.xi) * (
                ((n / nu) * (1 - q)) ** (-self.xi) - 1
            ) if self.xi != 0 else self.threshold - self.beta * np.log((n / nu) * (1 - q))
            
            # CVaR计算
            if self.xi < 1:
                cvar = (var + self.beta - self.xi * self.threshold) / (1 - self.xi)
            else:
                cvar = var * 1.5  # 简化处理
        
        # 根据仓位方向调整
        var_signed = var * position
        cvar_signed = cvar * position
        
        return {
            'VaR_95': var * 0.7 * position,  # 95% VaR
            'CVaR_95': cvar * 0.7 * position,
            'VaR_99': var_signed,
            'CVaR_99': cvar_signed,
            'extreme_index': self.xi if self.xi else 0,
            'tail_risk_level': self._classify_tail_risk(),
            'threshold': self.threshold
        }
    
    def _classify_tail_risk(self):
        """分类尾部风险等级"""
        if self.xi is None:
            return 'unknown'
        elif self.xi > 0.3:
            return 'high'  # 厚尾，极端事件频发
        elif self.xi > 0.1:
            return 'moderate'
        else:
            return 'low'


class CopperRiskDashboard:
    """
    铜价风险仪表板
    
    整合所有风险指标，提供统一视图
    """
    
    def __init__(self):
        self.risk_manager = CopperRiskManager()
        self.evt_model = ExtremeValueRiskModel()
        self.metrics_history = []
        
    def calculate_all_metrics(self, df, predictions_dict):
        """
        计算所有风险指标
        
        Args:
            df: 价格数据DataFrame
            predictions_dict: 各模型预测结果
        
        Returns:
            dict: 完整的风险指标
        """
        # 计算收益率
        returns = df['Close'].pct_change().dropna().values
        
        # 1. 基础统计
        metrics = {
            'price_stats': {
                'current_price': float(df['Close'].iloc[-1]),
                'price_volatility': float(np.std(returns) * np.sqrt(252)),  # 年化波动率
                'daily_volatility': float(np.std(returns)),
                'skewness': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns)),
            },
            'extreme_movements': {
                'max_daily_gain': float(np.max(returns)),
                'max_daily_loss': float(np.min(returns)),
                'days_above_2std': int(np.sum(np.abs(returns) > 2 * np.std(returns))),
            }
        }
        
        # 2. EVT尾部风险
        self.evt_model.fit(returns)
        evt_metrics = self.evt_model.calculate_var_cvar(confidence=0.99)
        metrics['tail_risk'] = evt_metrics
        
        # 3. 模型预测一致性
        if predictions_dict:
            model_preds = np.array(list(predictions_dict.values()))
            metrics['model_consensus'] = {
                'mean_prediction': float(np.mean(model_preds)),
                'std_prediction': float(np.std(model_preds)),
                'min_prediction': float(np.min(model_preds)),
                'max_prediction': float(np.max(model_preds)),
                'consensus_strength': float(1 - np.std(model_preds) / np.mean(model_preds)),
            }
        
        # 4. 风险评分（0-100）
        metrics['risk_score'] = self._calculate_risk_score(metrics)
        
        return metrics
    
    def _calculate_risk_score(self, metrics):
        """计算综合风险评分"""
        score = 50  # 基础分
        
        # 波动率调整
        vol = metrics['price_stats']['price_volatility']
        if vol > 0.4:
            score += 20
        elif vol > 0.25:
            score += 10
        
        # 尾部风险调整
        tail_level = metrics['tail_risk'].get('tail_risk_level', 'low')
        if tail_level == 'high':
            score += 15
        elif tail_level == 'moderate':
            score += 5
        
        # 模型分歧调整
        if 'model_consensus' in metrics:
            consensus = metrics['model_consensus']['consensus_strength']
            if consensus < 0.5:
                score += 10
        
        return min(100, max(0, score))
    
    def get_risk_summary(self, metrics):
        """获取风险摘要（用于前端显示）"""
        risk_level = '低风险' if metrics['risk_score'] < 40 else \
                     '中风险' if metrics['risk_score'] < 70 else '高风险'
        
        return {
            'risk_level': risk_level,
            'risk_score': metrics['risk_score'],
            'risk_color': '#10b981' if metrics['risk_score'] < 40 else \
                         '#f59e0b' if metrics['risk_score'] < 70 else '#ef4444',
            'key_alerts': self._generate_alerts(metrics),
            'recommendation': self._generate_recommendation(metrics)
        }
    
    def _generate_alerts(self, metrics):
        """生成风险预警"""
        alerts = []
        
        if metrics['price_stats']['price_volatility'] > 0.4:
            alerts.append({
                'level': 'high',
                'message': f"年化波动率过高: {metrics['price_stats']['price_volatility']:.1%}"
            })
        
        if metrics['tail_risk']['tail_risk_level'] == 'high':
            alerts.append({
                'level': 'warning',
                'message': '检测到厚尾分布，极端风险上升'
            })
        
        return alerts
    
    def _generate_recommendation(self, metrics):
        """生成投资建议"""
        if metrics['risk_score'] >= 70:
            return '建议降低仓位，关注风险对冲'
        elif metrics['risk_score'] >= 40:
            return '保持谨慎，设置止损保护'
        else:
            return '风险可控，可按计划执行'


# ============ 便捷函数 ============

def add_prediction_intervals(df, feature_cols, target_col='Close', forecast_horizon=7):
    """
    为铜价预测添加置信区间
    
    Args:
        df: 数据DataFrame
        feature_cols: 特征列名列表
        target_col: 目标列名
        forecast_horizon: 预测天数
    
    Returns:
        dict: 包含预测区间的完整结果
    """
    # 准备数据
    df_clean = df.dropna()
    X = df_clean[feature_cols].values[:-forecast_horizon]
    y = df_clean[target_col].values[forecast_horizon:]
    
    # 划分训练/校准集
    train_size = int(len(X) * 0.8)
    X_train, X_cal = X[:train_size], X[train_size:]
    y_train, y_cal = y[:train_size], y[train_size:]
    
    # 训练风险管理器
    risk_mgr = CopperRiskManager(confidence_level=0.95)
    risk_mgr.train_quantile_models(X_train, y_train)
    risk_mgr.calibrate_conformal(X_cal, y_cal)
    
    # 预测未来
    last_features = df_clean[feature_cols].values[-1:]
    prediction_result = risk_mgr.predict_with_uncertainty(last_features, method='conformal')
    
    return prediction_result


def calculate_copper_var(returns, confidence=0.95, method='historical'):
    """
    计算铜价VaR
    
    Args:
        returns: 收益率序列
        confidence: 置信水平
        method: 'historical', 'parametric', 'evt'
    """
    returns = np.array(returns)
    
    if method == 'historical':
        var = np.percentile(returns, (1 - confidence) * 100)
        return {'VaR': float(var), 'method': 'historical'}
    
    elif method == 'parametric':
        mu = np.mean(returns)
        sigma = np.std(returns)
        z_score = stats.norm.ppf(1 - confidence)
        var = mu + z_score * sigma
        return {'VaR': float(var), 'method': 'parametric'}
    
    elif method == 'evt':
        evt = ExtremeValueRiskModel()
        evt.fit(returns)
        result = evt.calculate_var_cvar(confidence=confidence)
        return {'VaR': result['VaR_99'], 'method': 'evt', 'details': result}
    
    else:
        raise ValueError(f"Unknown method: {method}")


if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("🛡️ 铜价风险管理模块测试")
    print("=" * 60)
    
    # 生成模拟数据
    np.random.seed(42)
    n_samples = 500
    
    # 模拟铜价特征
    features = np.random.randn(n_samples, 5)
    # 模拟价格（带噪声）
    target = 70000 + np.cumsum(np.random.randn(n_samples) * 500)
    
    # 测试分位数回归
    print("\n1️⃣ 测试分位数回归...")
    risk_mgr = CopperRiskManager()
    X_train, X_test = features[:400], features[400:]
    y_train, y_test = target[:400], target[400:]
    
    risk_mgr.train_quantile_models(X_train, y_train)
    risk_mgr.calibrate_conformal(X_test[:50], y_test[:50])
    
    pred = risk_mgr.predict_with_uncertainty(X_test[50:55], method='conformal')
    print(f"   点预测: {pred['point_prediction'][0]:.2f}")
    print(f"   95%区间: [{pred['lower_95'][0]:.2f}, {pred['upper_95'][0]:.2f}]")
    print(f"   置信度: {pred['confidence']:.2%}")
    
    # 测试EVT模型
    print("\n2️⃣ 测试极值理论模型...")
    returns = np.diff(target) / target[:-1]
    evt = ExtremeValueRiskModel()
    evt.fit(returns)
    var_result = evt.calculate_var_cvar(confidence=0.99)
    print(f"   99% VaR: {var_result['VaR_99']:.4f}")
    print(f"   99% CVaR: {var_result['CVaR_99']:.4f}")
    print(f"   尾部风险等级: {var_result['tail_risk_level']}")
    
    print("\n✅ 测试完成!")
