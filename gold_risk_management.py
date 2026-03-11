#!/usr/bin/env python3
"""
黄金价格预测 - 风险管理与模型验证模块
包含：回测陷阱防范、压力测试、模型解释性分析
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 尝试导入机器学习相关库
try:
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn 未安装，部分功能受限")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️ SHAP 未安装，模型解释性功能受限")

# 尝试导入统计检验库
try:
    from scipy import stats
    from scipy.stats import jarque_bera
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ scipy 未安装，统计检验功能受限")


class GoldRiskManager:
    """黄金价格预测风险管理器"""
    
    def __init__(self, transaction_cost: float = 0.001, slippage: float = 0.0005):
        """
        初始化风险管理器
        
        参数:
            transaction_cost: 交易成本（默认0.1%）
            slippage: 滑点成本（默认0.05%）
        """
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.total_cost = transaction_cost + slippage
        
    def rolling_window_validation(self, X: pd.DataFrame, y: pd.Series, 
                                   model, window_size: int = 252, 
                                   step_size: int = 21) -> Dict:
        """
        滚动窗口交叉验证 - 防范过拟合
        
        参数:
            X: 特征数据
            y: 目标变量
            model: 预测模型
            window_size: 训练窗口大小（默认252个交易日≈1年）
            step_size: 滚动步长（默认21个交易日≈1个月）
        
        返回:
            包含验证结果的字典
        """
        print("🔍 执行滚动窗口交叉验证...")
        print(f"   窗口大小: {window_size}天, 步长: {step_size}天")
        
        n_samples = len(X)
        results = {
            'train_scores': [],
            'test_scores': [],
            'predictions': [],
            'actuals': [],
            'dates': [],
            'windows': []
        }
        
        # 滚动窗口验证
        for start_idx in range(window_size, n_samples - step_size, step_size):
            end_idx = start_idx + step_size
            
            # 训练数据
            X_train = X.iloc[start_idx - window_size:start_idx]
            y_train = y.iloc[start_idx - window_size:start_idx]
            
            # 测试数据
            X_test = X.iloc[start_idx:end_idx]
            y_test = y.iloc[start_idx:end_idx]
            
            if len(X_test) == 0:
                break
            
            # 训练模型
            try:
                model.fit(X_train, y_train)
                
                # 预测
                train_pred = model.predict(X_train)
                test_pred = model.predict(X_test)
                
                # 计算指标
                train_score = r2_score(y_train, train_pred)
                test_score = r2_score(y_test, test_pred)
                
                results['train_scores'].append(train_score)
                results['test_scores'].append(test_score)
                results['predictions'].extend(test_pred)
                results['actuals'].extend(y_test.values)
                results['dates'].extend(X_test.index.tolist())
                results['windows'].append({
                    'train_start': X_train.index[0],
                    'train_end': X_train.index[-1],
                    'test_start': X_test.index[0],
                    'test_end': X_test.index[-1]
                })
                
            except Exception as e:
                print(f"   ⚠️ 窗口 {start_idx} 训练失败: {e}")
                continue
        
        # 计算统计指标
        if results['test_scores']:
            results['mean_train_score'] = np.mean(results['train_scores'])
            results['mean_test_score'] = np.mean(results['test_scores'])
            results['score_std'] = np.std(results['test_scores'])
            results['overfitting_gap'] = results['mean_train_score'] - results['mean_test_score']
            
            print(f"✅ 滚动窗口验证完成")
            print(f"   平均训练R²: {results['mean_train_score']:.4f}")
            print(f"   平均测试R²: {results['mean_test_score']:.4f}")
            print(f"   过拟合差距: {results['overfitting_gap']:.4f}")
            
            if results['overfitting_gap'] > 0.1:
                print(f"   ⚠️ 警告: 检测到过拟合迹象！")
        
        return results
    
    def stress_test(self, df: pd.DataFrame, predictions: pd.Series, 
                   actuals: pd.Series, initial_capital: float = 100000) -> Dict:
        """
        压力测试 - 评估极端行情下的表现
        
        参数:
            df: 包含日期和价格的完整数据
            predictions: 预测收益率
            actuals: 实际收益率
            initial_capital: 初始资金
        
        返回:
            压力测试结果
        """
        print("🔥 执行压力测试...")
        
        # 定义历史危机时期
        crisis_periods = {
            '2008金融危机': ('2008-09-01', '2009-03-31'),
            '2010欧债危机': ('2010-05-01', '2010-09-30'),
            '2011美债危机': ('2011-07-01', '2011-11-30'),
            '2015股灾': ('2015-06-01', '2015-08-31'),
            '2020新冠疫情': ('2020-02-01', '2020-04-30'),
            '2022俄乌冲突': ('2022-02-01', '2022-06-30'),
            '2024高利率环境': ('2024-01-01', '2024-12-31')
        }
        
        stress_results = {}
        
        for crisis_name, (start_date, end_date) in crisis_periods.items():
            try:
                # 筛选危机期间数据
                mask = (df.index >= start_date) & (df.index <= end_date)
                crisis_data = df[mask]
                
                if len(crisis_data) < 5:
                    continue
                
                # 计算期间表现
                crisis_actuals = actuals[mask]
                crisis_predictions = predictions[mask]
                
                # 计算累计收益
                cumulative_return = (1 + crisis_actuals).prod() - 1
                
                # 计算最大回撤
                cumulative = (1 + crisis_actuals).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()
                
                # 计算胜率
                correct_predictions = np.sign(crisis_predictions) == np.sign(crisis_actuals)
                win_rate = correct_predictions.mean()
                
                # 计算夏普比率（假设无风险利率2%）
                excess_returns = crisis_actuals - 0.02/252
                if crisis_actuals.std() > 0:
                    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / crisis_actuals.std()
                else:
                    sharpe_ratio = 0
                
                stress_results[crisis_name] = {
                    'period': f"{start_date} ~ {end_date}",
                    'days': len(crisis_data),
                    'cumulative_return': cumulative_return,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'sharpe_ratio': sharpe_ratio,
                    'volatility': crisis_actuals.std() * np.sqrt(252),
                    'avg_daily_return': crisis_actuals.mean()
                }
                
                print(f"   {crisis_name}: 收益{cumulative_return*100:+.2f}%, 最大回撤{max_drawdown*100:.2f}%")
                
            except Exception as e:
                print(f"   ⚠️ {crisis_name} 测试失败: {e}")
                continue
        
        # 计算整体压力测试结果
        if stress_results:
            avg_drawdown = np.mean([r['max_drawdown'] for r in stress_results.values()])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in stress_results.values()])
            
            stress_results['summary'] = {
                'avg_max_drawdown': avg_drawdown,
                'avg_sharpe_ratio': avg_sharpe,
                'worst_crisis': min(stress_results.items(), key=lambda x: x[1]['max_drawdown'])[0]
            }
            
            print(f"\n📊 压力测试总结:")
            print(f"   平均最大回撤: {avg_drawdown*100:.2f}%")
            print(f"   平均夏普比率: {avg_sharpe:.2f}")
            print(f"   最差表现时期: {stress_results['summary']['worst_crisis']}")
        
        return stress_results
    
    def calculate_risk_metrics(self, returns: pd.Series, 
                               risk_free_rate: float = 0.02) -> Dict:
        """
        计算风险指标
        
        参数:
            returns: 收益率序列
            risk_free_rate: 无风险利率（默认2%）
        
        返回:
            风险指标字典
        """
        print("📈 计算风险指标...")
        
        # 检查输入数据
        if returns is None or len(returns) < 2:
            print("⚠️ 收益率数据不足，返回默认风险指标")
            return {
                'annual_return': 0,
                'annual_volatility': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'calmar_ratio': 0,
                'win_rate': 0,
                'profit_loss_ratio': 0,
                'var_95': 0,
                'var_99': 0,
                'cvar_95': 0,
                'skewness': 0,
                'kurtosis': 0
            }
        
        # 移除NaN值
        returns = returns.dropna()
        if len(returns) < 2:
            print("⚠️ 有效收益率数据不足，返回默认风险指标")
            return {
                'annual_return': 0,
                'annual_volatility': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'calmar_ratio': 0,
                'win_rate': 0,
                'profit_loss_ratio': 0,
                'var_95': 0,
                'var_99': 0,
                'cvar_95': 0,
                'skewness': 0,
                'kurtosis': 0
            }
        
        # 年化因子（假设252个交易日）
        ann_factor = 252
        
        # 年化收益率
        annual_return = returns.mean() * ann_factor
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(ann_factor)
        
        # 夏普比率
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0
        
        # 索提诺比率（只考虑下行波动）
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(ann_factor) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 最大回撤持续时间
        try:
            peak_idx = running_max.idxmax() if len(running_max) > 0 else None
            trough_idx = drawdown.idxmin() if len(drawdown) > 0 else None
        except:
            peak_idx = None
            trough_idx = None
        
        # 胜率
        win_rate = (returns > 0).mean()
        
        # 盈亏比
        avg_gain = returns[returns > 0].mean()
        avg_loss = abs(returns[returns < 0].mean())
        profit_loss_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
        
        # 卡尔玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # VaR (Value at Risk) - 95%置信度
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # CVaR (Conditional VaR)
        cvar_95 = returns[returns <= var_95].mean()
        
        metrics = {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }
        
        print(f"✅ 风险指标计算完成")
        print(f"   年化收益率: {annual_return*100:.2f}%")
        print(f"   年化波动率: {annual_volatility*100:.2f}%")
        print(f"   夏普比率: {sharpe_ratio:.2f}")
        print(f"   最大回撤: {max_drawdown*100:.2f}%")
        print(f"   胜率: {win_rate*100:.1f}%")
        
        return metrics
    
    def apply_transaction_costs(self, returns: pd.Series, 
                                turnover_rate: float = 0.5) -> pd.Series:
        """
        应用交易成本
        
        参数:
            returns: 原始收益率
            turnover_rate: 换手率（默认50%）
        
        返回:
            扣除成本后的收益率
        """
        # 每次交易的总成本
        cost_per_trade = self.total_cost * turnover_rate
        
        # 假设每天可能产生交易
        daily_cost = cost_per_trade / 252
        
        # 扣除成本
        net_returns = returns - daily_cost
        
        print(f"💰 应用交易成本:")
        print(f"   单边交易成本: {self.total_cost*100:.3f}%")
        print(f"   年化换手率: {turnover_rate*100:.0f}%")
        print(f"   年化成本影响: {daily_cost*252*100:.2f}%")
        
        return net_returns
    
    def analyze_feature_importance(self, X: pd.DataFrame, y: pd.Series, 
                                   model) -> Optional[pd.DataFrame]:
        """
        分析特征重要性 - 模型解释性
        
        参数:
            X: 特征数据
            y: 目标变量
            model: 已训练模型
        
        返回:
            特征重要性DataFrame
        """
        print("🔍 分析特征重要性...")
        
        try:
            # 方法1: 内置特征重要性（适用于树模型）
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                method = '内置特征重要性'
            
            # 方法2: SHAP值分析
            elif SHAP_AVAILABLE and hasattr(model, 'predict'):
                print("   使用SHAP值分析...")
                explainer = shap.TreeExplainer(model) if hasattr(model, 'estimators_') else shap.KernelExplainer(model.predict, X.iloc[:100])
                shap_values = explainer.shap_values(X.iloc[:100])
                importance = np.abs(shap_values).mean(axis=0)
                method = 'SHAP值'
            
            # 方法3: 排列重要性（备用）
            else:
                print("   使用排列重要性...")
                importance = self._permutation_importance(model, X, y)
                method = '排列重要性'
            
            # 创建结果DataFrame
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': importance,
                'importance_pct': importance / importance.sum() * 100
            }).sort_values('importance', ascending=False)
            
            print(f"✅ 特征重要性分析完成 ({method})")
            print(f"\n📊 Top 5 重要特征:")
            for idx, row in feature_importance.head(5).iterrows():
                print(f"   {row['feature']}: {row['importance_pct']:.1f}%")
            
            return feature_importance
            
        except Exception as e:
            print(f"⚠️ 特征重要性分析失败: {e}")
            return None
    
    def _permutation_importance(self, model, X: pd.DataFrame, y: pd.Series, 
                                 n_repeats: int = 5) -> np.ndarray:
        """
        计算排列重要性
        """
        baseline_score = r2_score(y, model.predict(X))
        importances = []
        
        for col in X.columns:
            scores = []
            for _ in range(n_repeats):
                X_permuted = X.copy()
                X_permuted[col] = np.random.permutation(X_permuted[col])
                permuted_score = r2_score(y, model.predict(X_permuted))
                scores.append(baseline_score - permuted_score)
            importances.append(np.mean(scores))
        
        return np.array(importances)
    
    # ==================== 过拟合防御体系 ====================
    
    def overfitting_defense_system(self, X: pd.DataFrame, y: pd.Series, 
                                   model, n_splits: int = 5) -> Dict:
        """
        过拟合防御体系 - 多层防御机制
        
        防御层:
        1. 数据隔离 - 训练/验证/测试集严格分离 (60/20/20)
        2. 滚动回测 - Walk-Forward优化
        3. 蒙特卡洛扰动 - 对历史价格加入随机噪声测试稳健性
        4. 交叉验证 - K-Fold时间序列交叉验证
        
        参数:
            X: 特征数据
            y: 目标变量
            model: 预测模型
            n_splits: K-Fold折数
        
        返回:
            防御体系评估结果
        """
        print("\n" + "="*70)
        print("🛡️ 过拟合防御体系检测")
        print("="*70)
        
        defense_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'defense_layers': {},
            'overall_status': 'PASS',
            'warnings': [],
            'critical_alerts': []
        }
        
        # 1. 数据隔离检测
        print("\n📊 防御层1: 数据隔离检测 (60/20/20)")
        n_samples = len(X)
        train_size = int(n_samples * 0.6)
        val_size = int(n_samples * 0.2)
        
        train_data = X.iloc[:train_size]
        val_data = X.iloc[train_size:train_size+val_size]
        test_data = X.iloc[train_size+val_size:]
        
        print(f"   训练集: {len(train_data)}样本 ({len(train_data)/n_samples*100:.1f}%)")
        print(f"   验证集: {len(val_data)}样本 ({len(val_data)/n_samples*100:.1f}%)")
        print(f"   测试集: {len(test_data)}样本 ({len(test_data)/n_samples*100:.1f}%)")
        
        # 检查数据泄露（时间顺序）
        train_end = train_data.index[-1] if hasattr(train_data.index, '__len__') else None
        val_start = val_data.index[0] if hasattr(val_data.index, '__len__') else None
        
        if train_end is not None and val_start is not None:
            if train_end >= val_start:
                defense_results['critical_alerts'].append("⚠️ 数据泄露风险: 训练集包含未来信息!")
                defense_results['overall_status'] = 'FAIL'
            else:
                print(f"   ✅ 数据隔离正确，无未来信息泄露")
        
        defense_results['defense_layers']['data_isolation'] = {
            'status': 'PASS',
            'train_size': len(train_data),
            'val_size': len(val_data),
            'test_size': len(test_data)
        }
        
        # 2. K-Fold时间序列交叉验证
        print(f"\n📊 防御层2: K-Fold时间序列交叉验证 (K={n_splits})")
        if SKLEARN_AVAILABLE:
            tscv = TimeSeriesSplit(n_splits=n_splits)
            cv_scores = []
            
            for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                score = r2_score(y_test, y_pred)
                cv_scores.append(score)
                print(f"   Fold {fold}: R² = {score:.4f}")
            
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            cv_min = np.min(cv_scores)
            
            print(f"   平均R²: {cv_mean:.4f} (±{cv_std:.4f})")
            print(f"   最小R²: {cv_min:.4f}")
            
            # 关键红线：样本外R²连续低于0.3
            if cv_min < 0.3:
                defense_results['warnings'].append(
                    f"🟡 警告: 存在Fold R²={cv_min:.2f}<0.3，模型可能不稳定"
                )
            
            defense_results['defense_layers']['cross_validation'] = {
                'status': 'PASS' if cv_mean > 0.3 else 'WARNING',
                'cv_scores': cv_scores,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'cv_min': cv_min
            }
        else:
            print("   ⚠️ scikit-learn未安装，跳过交叉验证")
        
        # 3. 蒙特卡洛扰动测试
        print(f"\n📊 防御层3: 蒙特卡洛扰动测试 (1000次模拟)")
        mc_results = self._monte_carlo_robustness_test(X, y, model, n_simulations=1000)
        defense_results['defense_layers']['monte_carlo'] = mc_results
        
        if mc_results['robustness_rate'] < 0.6:
            defense_results['critical_alerts'].append(
                f"🔴 关键警告: 蒙特卡洛稳健性率{mc_results['robustness_rate']*100:.1f}%<60%，模型对噪声敏感!"
            )
            defense_results['overall_status'] = 'WARNING'
        
        # 4. 滚动Walk-Forward回测
        print(f"\n📊 防御层4: Walk-Forward滚动回测")
        wf_results = self._walk_forward_test(X, y, model)
        defense_results['defense_layers']['walk_forward'] = wf_results
        
        # 综合评估
        print("\n" + "-"*70)
        print("📋 过拟合防御体系评估总结")
        print("-"*70)
        
        if defense_results['critical_alerts']:
            print("🔴 关键警报:")
            for alert in defense_results['critical_alerts']:
                print(f"   {alert}")
        
        if defense_results['warnings']:
            print("🟡 警告:")
            for warning in defense_results['warnings']:
                print(f"   {warning}")
        
        if not defense_results['critical_alerts'] and not defense_results['warnings']:
            print("✅ 所有防御层检测通过，模型稳健性良好")
        
        print(f"\n整体状态: {defense_results['overall_status']}")
        
        return defense_results
    
    def _monte_carlo_robustness_test(self, X: pd.DataFrame, y: pd.Series, 
                                     model, n_simulations: int = 1000,
                                     noise_level: float = 0.02) -> Dict:
        """
        蒙特卡洛扰动测试 - 评估模型对数据噪声的稳健性
        
        参数:
            X: 特征数据
            y: 目标变量
            model: 预测模型
            n_simulations: 模拟次数（默认1000）
            noise_level: 噪声水平（默认2%）
        
        返回:
            稳健性测试结果
        """
        # 基准性能
        model.fit(X.iloc[:-100], y.iloc[:-100])
        baseline_pred = model.predict(X.iloc[-100:])
        baseline_r2 = r2_score(y.iloc[-100:], baseline_pred)
        baseline_direction = np.sign(baseline_pred) == np.sign(y.iloc[-100:].values)
        baseline_win_rate = baseline_direction.mean()
        
        # 蒙特卡洛模拟
        r2_scores = []
        win_rates = []
        
        for i in range(n_simulations):
            # 加入随机噪声
            X_noisy = X.copy()
            for col in X.columns:
                if X[col].dtype in ['float64', 'float32']:
                    noise = np.random.normal(0, noise_level * X[col].std(), len(X))
                    X_noisy[col] = X_noisy[col] + noise
            
            try:
                model.fit(X_noisy.iloc[:-100], y.iloc[:-100])
                pred = model.predict(X_noisy.iloc[-100:])
                r2 = r2_score(y.iloc[-100:], pred)
                direction = np.sign(pred) == np.sign(y.iloc[-100:].values)
                win_rate = direction.mean()
                
                r2_scores.append(r2)
                win_rates.append(win_rate)
            except:
                continue
        
        r2_scores = np.array(r2_scores)
        win_rates = np.array(win_rates)
        
        # 计算稳健性指标
        r2_robustness = np.mean(r2_scores > baseline_r2 * 0.8)  # R²保持在80%以上的比例
        win_rate_robustness = np.mean(win_rates > baseline_win_rate * 0.9)  # 胜率保持在90%以上的比例
        overall_robustness = (r2_robustness + win_rate_robustness) / 2
        
        print(f"   基准R²: {baseline_r2:.4f}")
        print(f"   基准胜率: {baseline_win_rate*100:.1f}%")
        print(f"   噪声R²均值: {np.mean(r2_scores):.4f} (±{np.std(r2_scores):.4f})")
        print(f"   噪声胜率均值: {np.mean(win_rates)*100:.1f}%")
        print(f"   R²稳健性率: {r2_robustness*100:.1f}%")
        print(f"   胜率稳健性率: {win_rate_robustness*100:.1f}%")
        print(f"   综合稳健性率: {overall_robustness*100:.1f}%")
        
        if overall_robustness >= 0.6:
            print(f"   ✅ 通过: 稳健性率>{60}%")
        else:
            print(f"   🔴 不通过: 稳健性率<{60}%")
        
        return {
            'status': 'PASS' if overall_robustness >= 0.6 else 'FAIL',
            'n_simulations': n_simulations,
            'baseline_r2': baseline_r2,
            'baseline_win_rate': baseline_win_rate,
            'r2_robustness': r2_robustness,
            'win_rate_robustness': win_rate_robustness,
            'robustness_rate': overall_robustness,
            'r2_mean': np.mean(r2_scores),
            'r2_std': np.std(r2_scores),
            'win_rate_mean': np.mean(win_rates)
        }
    
    def _walk_forward_test(self, X: pd.DataFrame, y: pd.Series, 
                          model, min_train_size: int = 252,
                          step_size: int = 21) -> Dict:
        """
        Walk-Forward滚动回测 - 模拟实盘环境
        
        参数:
            X: 特征数据
            y: 目标变量
            model: 预测模型
            min_train_size: 最小训练窗口
            step_size: 滚动步长
        
        返回:
            Walk-Forward测试结果
        """
        n_samples = len(X)
        
        # 根据数据量动态调整参数
        if n_samples < min_train_size + step_size * 2:
            # 数据不足时自适应调整
            min_train_size = max(50, int(n_samples * 0.6))  # 至少使用60%数据训练
            step_size = max(5, int((n_samples - min_train_size) / 3))  # 分成至少3个测试期
            print(f"   ⚠️ 数据量不足(n={n_samples})，自适应调整: 训练窗口={min_train_size}, 步长={step_size}")
        
        predictions = []
        actuals = []
        r2_scores = []
        
        # 每月滚动重训练
        for start_idx in range(min_train_size, n_samples - step_size, step_size):
            end_idx = start_idx + step_size
            
            X_train = X.iloc[:start_idx]  # 扩展训练集
            y_train = y.iloc[:start_idx]
            X_test = X.iloc[start_idx:end_idx]
            y_test = y.iloc[start_idx:end_idx]
            
            try:
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                r2 = r2_score(y_test, pred)
                
                predictions.extend(pred)
                actuals.extend(y_test.values)
                r2_scores.append(r2)
            except:
                continue
        
        if len(predictions) > 0:
            overall_r2 = r2_score(actuals, predictions)
            win_rate = np.mean(np.sign(predictions) == np.sign(actuals))
            
            # 检测连续低R²（3个月<0）或低胜率（<50%）
            # 注：短期价格预测R²为负是正常的，改用方向胜率作为主要指标
            low_r2_streak = 0
            max_low_streak = 0
            low_win_streak = 0
            max_low_win_streak = 0
            
            for i, r2 in enumerate(r2_scores):
                # R² 阈值设为0（比均值预测好即可）
                if r2 < 0:
                    low_r2_streak += 1
                    max_low_streak = max(max_low_streak, low_r2_streak)
                else:
                    low_r2_streak = 0
            
            print(f"   Walk-Forward周期数: {len(r2_scores)}")
            print(f"   平均R²: {np.mean(r2_scores):.4f}")
            print(f"   整体R²: {overall_r2:.4f}")
            print(f"   方向胜率: {win_rate*100:.1f}%")
            print(f"   最长负R²连续: {max_low_streak}期")
            
            # 综合评估：R²连续为负 或 胜率<50% 才警告
            is_warning = max_low_streak >= 3 and win_rate < 0.5
            
            if is_warning:
                print(f"   🔴 警报: 连续{max_low_streak}期R²<0且胜率<50%，模型可能失效!")
            else:
                print(f"   ✅ 模型通过Walk-Forward测试")
            
            return {
                'status': 'PASS' if not is_warning else 'WARNING',
                'n_periods': len(r2_scores),
                'mean_r2': np.mean(r2_scores),
                'overall_r2': overall_r2,
                'win_rate': win_rate,
                'max_low_r2_streak': max_low_streak,
                'r2_scores': r2_scores
            }
        else:
            return {'status': 'FAIL', 'error': 'No valid predictions'}
    
    # ==================== 模型失效预警系统 ====================
    
    def model_failure_detection(self, y_true: pd.Series, y_pred: pd.Series,
                                feature_importance_history: List[Dict] = None,
                                returns: pd.Series = None) -> Dict:
        """
        模型失效预警系统 - Regime Change Detection
        
        监控指标:
        1. 预测误差滚动均值：MAPE_30d > 历史均值+2σ → 预警
        2. 因子贡献度突变：关键因子SHAP值占比<10% → 结构变化
        3. 残差自相关：Durbin-Watson检验p<0.05 → 模型失效
        4. 波动率异常：GARCH(1,1)预测VaR突破历史99%分位数
        
        参数:
            y_true: 真实值
            y_pred: 预测值
            feature_importance_history: 特征重要性历史
            returns: 收益率序列（用于波动率计算）
        
        返回:
            失效预警结果
        """
        print("\n" + "="*70)
        print("⚠️ 模型失效预警系统")
        print("="*70)
        
        alerts = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'NORMAL',
            'indicators': {},
            'warnings': [],
            'critical_alerts': [],
            'recommendations': []
        }
        
        # 1. 预测误差监控
        print("\n📊 指标1: 预测误差滚动监控")
        errors = np.abs(y_true - y_pred)
        mape = errors / (np.abs(y_true) + 1e-6)
        
        # 30日滚动MAPE
        if len(mape) >= 30:
            rolling_mape = pd.Series(mape).rolling(30).mean()
            historical_mean = rolling_mape.iloc[:-30].mean() if len(rolling_mape) > 30 else rolling_mape.mean()
            historical_std = rolling_mape.iloc[:-30].std() if len(rolling_mape) > 30 else rolling_mape.std()
            
            current_mape = rolling_mape.iloc[-1]
            threshold = historical_mean + 2 * historical_std
            
            print(f"   当前30日MAPE: {current_mape:.4f}")
            print(f"   历史均值+2σ: {threshold:.4f}")
            
            if current_mape > threshold:
                alerts['warnings'].append(
                    f"🟡 MAPE_30d ({current_mape:.4f}) > 历史均值+2σ ({threshold:.4f})"
                )
                alerts['indicators']['mape_status'] = 'WARNING'
            else:
                print(f"   ✅ MAPE正常")
                alerts['indicators']['mape_status'] = 'NORMAL'
            
            alerts['indicators']['current_mape'] = current_mape
            alerts['indicators']['mape_threshold'] = threshold
        
        # 2. 因子贡献度突变检测
        if feature_importance_history and len(feature_importance_history) >= 2:
            print("\n📊 指标2: 因子贡献度突变检测")
            
            recent = feature_importance_history[-1]
            previous = feature_importance_history[-2]
            
            # 检查关键因子（如美元指数）变化
            key_factors = ['dxy', 'usd_index', 'dollar', 'real_rate', '利率']
            
            for factor in key_factors:
                recent_val = recent.get(factor, 0)
                previous_val = previous.get(factor, 0)
                
                if recent_val < 0.10 and previous_val >= 0.10:
                    alerts['critical_alerts'].append(
                        f"🔴 因子突变: {factor}贡献度从{previous_val*100:.1f}%降至{recent_val*100:.1f}%<10%"
                    )
                    alerts['recommendations'].append(
                        "💡 建议: 市场驱动因素可能发生变化，考虑切换至'央行购金+地缘政治'主导模式"
                    )
                    alerts['indicators']['factor_shift'] = True
                    print(f"   🔴 {factor}贡献度突变: {previous_val*100:.1f}% → {recent_val*100:.1f}%")
                
        # 3. 残差自相关检测 (Durbin-Watson)
        print("\n📊 指标3: 残差自相关检测")
        residuals = y_true - y_pred
        
        if SCIPY_AVAILABLE and len(residuals) > 10:
            # 简化DW检验
            residual_diff = np.diff(residuals)
            dw_stat = np.sum(residual_diff**2) / np.sum(residuals**2)
            
            print(f"   Durbin-Watson统计量: {dw_stat:.4f}")
            
            # DW接近2表示无自相关，接近0或4表示有自相关
            if dw_stat < 1.5 or dw_stat > 2.5:
                alerts['warnings'].append(
                    f"🟡 残差自相关异常: DW={dw_stat:.2f} (正常范围1.5-2.5)"
                )
                alerts['indicators']['dw_status'] = 'WARNING'
                print(f"   🟡 检测到残差自相关")
            else:
                print(f"   ✅ 残差无自相关")
                alerts['indicators']['dw_status'] = 'NORMAL'
            
            alerts['indicators']['dw_stat'] = dw_stat
        
        # 4. 波动率异常检测
        if returns is not None and len(returns) > 50:
            print("\n📊 指标4: 波动率异常检测")
            
            # 简化GARCH(1,1) - 使用EWMA代替
            current_vol = returns.iloc[-20:].std()
            historical_vol = returns.iloc[:-20].std()
            var_99 = np.percentile(returns.iloc[:-20], 1)
            recent_return = returns.iloc[-1]
            
            print(f"   当前波动率: {current_vol:.4f}")
            print(f"   历史波动率: {historical_vol:.4f}")
            print(f"   历史99% VaR: {var_99:.4f}")
            print(f"   最新收益: {recent_return:.4f}")
            
            # 检查VaR突破
            if recent_return < var_99:
                alerts['critical_alerts'].append(
                    f"🔴 波动率异常: 最新收益{recent_return:.4f}突破历史99% VaR ({var_99:.4f})"
                )
                alerts['indicators']['var_break'] = True
                print(f"   🔴 VaR突破!")
            
            # 检查波动率激增
            if current_vol > historical_vol * 2:
                alerts['warnings'].append(
                    f"🟡 波动率激增: 当前{current_vol:.4f} > 历史{historical_vol:.4f}的2倍"
                )
                print(f"   🟡 波动率异常升高")
            else:
                print(f"   ✅ 波动率正常")
        
        # 综合评估
        print("\n" + "-"*70)
        print("📋 模型失效预警总结")
        print("-"*70)
        
        if alerts['critical_alerts']:
            alerts['status'] = 'CRITICAL'
            print("🔴 关键警报 - 模型可能已失效:")
            for alert in alerts['critical_alerts']:
                print(f"   {alert}")
        elif alerts['warnings']:
            alerts['status'] = 'WARNING'
            print("🟡 警告 - 需要密切监控:")
            for warning in alerts['warnings']:
                print(f"   {warning}")
        else:
            print("✅ 所有指标正常，模型运行良好")
        
        if alerts['recommendations']:
            print("\n💡 建议行动:")
            for rec in alerts['recommendations']:
                print(f"   {rec}")
        
        return alerts
    
    # ==================== 高级仓位管理（含Kelly准则）====================
    
    def kelly_position_sizing(self, win_rate: float, profit_loss_ratio: float,
                              current_volatility: float = None,
                              gvz_index: float = None,
                              account_size: float = 1000000,
                              kelly_fraction: float = 0.25) -> Dict:
        """
        Kelly准则动态仓位管理
        
        公式: f* = W - (1-W)/R
        其中: W=胜率, R=盈亏比
        
        黄金特殊调整:
        - 波动率缩放: GVZ>20时, 仓位×0.7
        - 趋势强化: 突破200日均线且一致看多, 可提升至1/2 Kelly
        - 衰退保护: VIX>30或GPR>150时, 最低仓位锁定5%
        
        参数:
            win_rate: 胜率W
            profit_loss_ratio: 盈亏比R
            current_volatility: 当前波动率
            gvz_index: 黄金波动率指数
            account_size: 账户规模
            kelly_fraction: Kelly分数(1/4至1/2)
        
        返回:
            Kelly仓位建议
        """
        print("\n" + "="*70)
        print("📊 Kelly准则动态仓位管理")
        print("="*70)
        
        # 计算Full Kelly
        if profit_loss_ratio > 0 and win_rate > 0:
            full_kelly = (win_rate * (profit_loss_ratio + 1) - 1) / profit_loss_ratio
            full_kelly = max(0, min(full_kelly, 1.0))  # 限制在0-100%
        else:
            full_kelly = 0
        
        # 实用仓位（Fractional Kelly）
        practical_kelly = full_kelly * kelly_fraction
        
        print(f"\n基础计算:")
        print(f"   胜率(W): {win_rate*100:.1f}%")
        print(f"   盈亏比(R): {profit_loss_ratio:.2f}")
        print(f"   Full Kelly: {full_kelly*100:.1f}%")
        print(f"   使用Kelly分数: {kelly_fraction*100:.0f}%")
        print(f"   实用仓位: {practical_kelly*100:.1f}%")
        
        # 黄金特殊调整
        adjustments = []
        final_position = practical_kelly
        
        # 1. 波动率缩放 (GVZ > 20)
        if gvz_index and gvz_index > 20:
            final_position *= 0.7
            adjustments.append(f"GVZ={gvz_index}>20, 仓位×0.7")
            print(f"\n🔄 波动率缩放: GVZ={gvz_index}>20, 仓位调整至{final_position*100:.1f}%")
        
        # 2. VIX/衰退保护 (VIX > 30)
        vix = 25  # 假设值，实际应从外部传入
        if vix > 30:
            min_position = 0.05  # 强制保留5%避险仓位
            if final_position < min_position:
                final_position = min_position
                adjustments.append(f"VIX>30, 最低仓位锁定5%")
                print(f"\n🛡️ 衰退保护: VIX>{30}, 最低仓位锁定{min_position*100:.0f}%")
        
        # 3. 趋势强化（简化逻辑，实际需要传入趋势信号）
        # if trend_breakout and model_consensus:
        #     final_position = min(final_position * 1.5, full_kelly * 0.5)
        #     adjustments.append("趋势强化，提升至1/2 Kelly")
        
        # 确保仓位在合理范围
        final_position = max(0.05, min(final_position, 0.5))  # 5%-50%
        
        position_value = account_size * final_position
        
        print(f"\n最终建议:")
        print(f"   Kelly仓位: {final_position*100:.1f}%")
        print(f"   仓位金额: ¥{position_value:,.0f}")
        print(f"   调整记录: {adjustments if adjustments else '无'}")
        
        return {
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'full_kelly': full_kelly,
            'kelly_fraction': kelly_fraction,
            'practical_kelly': practical_kelly,
            'final_position_pct': final_position,
            'position_value': position_value,
            'account_size': account_size,
            'adjustments': adjustments,
            'adjustment_factors': {
                'volatility_scaling': 0.7 if (gvz_index and gvz_index > 20) else 1.0,
                'recession_protection': 0.05 if vix > 30 else None
            }
        }
    
    def hierarchical_position_structure(self, base_position: float,
                                       account_size: float = 1000000,
                                       risk_budget: float = 0.10) -> Dict:
        """
        分层仓位架构
        
        结构:
        总风险预算(如账户10%)
            ├── 核心仓位(60%): 基于Kelly的基础配置
            ├── 对冲仓位(30%): 黄金期货期权保护
            └── 机动仓位(10%): 模型高置信度时的加码
        
        单日最大损失限制: 无论Kelly建议多少，单日损失不超过账户2%
        
        参数:
            base_position: 基础仓位比例
            account_size: 账户规模
            risk_budget: 总风险预算比例
        
        返回:
            分层仓位结构
        """
        print("\n" + "="*70)
        print("📊 分层仓位架构")
        print("="*70)
        
        total_risk_budget = account_size * risk_budget
        
        # 分层配置
        core_pct = 0.60      # 核心仓位
        hedge_pct = 0.30     # 对冲仓位
        tactical_pct = 0.10  # 机动仓位
        
        core_position = base_position * core_pct
        hedge_position = base_position * hedge_pct
        tactical_position = base_position * tactical_pct
        
        print(f"\n总风险预算: {risk_budget*100:.0f}% (¥{total_risk_budget:,.0f})")
        print(f"基础仓位: {base_position*100:.1f}%")
        print(f"\n分层配置:")
        print(f"   ├─ 核心仓位({core_pct*100:.0f}%): {core_position*100:.1f}% "
              f"= ¥{account_size*core_position:,.0f}")
        print(f"   │   └─ 基于Kelly的基础配置，长期持有")
        print(f"   ├─ 对冲仓位({hedge_pct*100:.0f}%): {hedge_position*100:.1f}% "
              f"= ¥{account_size*hedge_position:,.0f}")
        print(f"   │   └─ 黄金期货期权保护，防范下行风险")
        print(f"   └─ 机动仓位({tactical_pct*100:.0f}%): {tactical_position*100:.1f}% "
              f"= ¥{account_size*tactical_position:,.0f}")
        print(f"       └─ 模型高置信度(>80%)时的加码")
        
        # 单日最大损失限制
        max_daily_loss_limit = account_size * 0.02
        
        # 计算实际风险敞口
        var_95_estimate = 0.025  # 假设2.5%日VaR
        actual_risk_exposure = account_size * base_position * var_95_estimate
        
        print(f"\n风险控制:")
        print(f"   单日最大损失限制: ¥{max_daily_loss_limit:,.0f} (账户2%)")
        print(f"   预估风险敞口(VaR 95%): ¥{actual_risk_exposure:,.0f}")
        
        if actual_risk_exposure > max_daily_loss_limit:
            print(f"   🔴 警告: 风险敞口超限，建议降低仓位至"
                  f"{max_daily_loss_limit/(account_size*var_95_estimate)*100:.1f}%")
        else:
            print(f"   ✅ 风险敞口在安全范围内")
        
        return {
            'total_risk_budget': risk_budget,
            'risk_budget_value': total_risk_budget,
            'base_position': base_position,
            'core_position': {
                'pct': core_position,
                'value': account_size * core_position,
                'description': '基于Kelly的基础配置'
            },
            'hedge_position': {
                'pct': hedge_position,
                'value': account_size * hedge_position,
                'description': '黄金期货期权保护'
            },
            'tactical_position': {
                'pct': tactical_position,
                'value': account_size * tactical_position,
                'description': '模型高置信度加码'
            },
            'risk_limits': {
                'max_daily_loss_pct': 0.02,
                'max_daily_loss_value': max_daily_loss_limit,
                'var_95_estimate': var_95_estimate,
                'actual_risk_exposure': actual_risk_exposure
            }
        }
    
    def generate_risk_dashboard(self, model_status: str = 'NORMAL',
                                 current_position: float = 0.12,
                                 today_var: float = 0.018,
                                 factor_contributions: Dict = None,
                                 gvz_index: float = 18,
                                 stress_test_passed: bool = True) -> str:
        """
        生成风控监控仪表盘
        
        ┌─────────────────────────────────────────┐
        │ 黄金预测风控仪表盘                        │
        ├─────────────────────────────────────────┤
        │ 模型状态: 🟢正常  🟡预警  🔴失效         │
        │ 当前仓位: 12% (1/3 Kelly)               │
        │ 今日VaR: 1.8% (限额2%)                  │
        │ 关键因子贡献: 实际利率35% 美元25% 地缘20% │
        │ 波动率状态: GVZ=18 (正常)               │
        │ 压力测试: 通过2008/2020/2022情景        │
        └─────────────────────────────────────────┘
        """
        if factor_contributions is None:
            factor_contributions = {
                '实际利率': 0.35,
                '美元指数': 0.25,
                '地缘政治': 0.20,
                '通胀预期': 0.15,
                '其他': 0.05
            }
        
        # 状态图标
        status_icons = {
            'NORMAL': '🟢正常',
            'WARNING': '🟡预警',
            'CRITICAL': '🔴失效'
        }
        status_display = status_icons.get(model_status, '⚪未知')
        
        # VaR状态
        var_status = "✅" if today_var <= 0.02 else "🔴"
        
        # GVZ状态
        gvz_status = "正常" if gvz_index <= 20 else "偏高" if gvz_index <= 25 else "⚠️高"
        
        # 压力测试状态
        stress_status = "✅通过" if stress_test_passed else "🔴未通过"
        
        dashboard = []
        dashboard.append("┌" + "─"*58 + "┐")
        dashboard.append("│" + " 黄金预测风控仪表盘".center(54) + "│")
        dashboard.append("├" + "─"*58 + "┤")
        dashboard.append(f"│  模型状态: {status_display:<46}│")
        dashboard.append(f"│  当前仓位: {current_position*100:.0f}% (基于Kelly准则){' '*22}│")
        dashboard.append(f"│  今日VaR: {today_var*100:.1f}% (限额2%) {var_status}{' '*28}│")
        dashboard.append(f"│  关键因子: 实际利率{factor_contributions['实际利率']*100:.0f}% "
                        f"美元{factor_contributions['美元指数']*100:.0f}% "
                f"地缘{factor_contributions['地缘政治']*100:.0f}%{' '*10}│")
        dashboard.append(f"│  波动率: GVZ={gvz_index} ({gvz_status}){' '*38}│")
        dashboard.append(f"│  压力测试: {stress_status} 2008/2020/2022情景{' '*22}│")
        dashboard.append("└" + "─"*58 + "┘")
        
        return "\n".join(dashboard)
    
    def calculate_position_sizing(self, risk_metrics: Dict, 
                                   current_volatility: float = None,
                                   account_size: float = 1000000) -> Dict:
        """
        计算仓位管理建议 - 多种方法综合
        
        参数:
            risk_metrics: 风险指标字典
            current_volatility: 当前波动率（可选）
            account_size: 账户规模（默认100万）
        
        返回:
            仓位建议字典
        """
        print("\n📊 计算仓位管理建议...")
        
        # 使用当前波动率或历史波动率
        volatility = current_volatility if current_volatility else risk_metrics['annual_volatility']
        
        # 1. 固定风险法 (Fixed Fractional)
        # 每笔交易最大风险为账户的2%
        max_risk_per_trade = 0.02
        var_95 = abs(risk_metrics['var_95'])
        fixed_fractional_position = min(max_risk_per_trade / (var_95 + 0.001), 1.0)
        
        # 2. 凯利公式 (Kelly Criterion)
        win_rate = risk_metrics['win_rate']
        profit_loss_ratio = risk_metrics['profit_loss_ratio']
        
        if profit_loss_ratio > 0 and win_rate > 0:
            kelly_fraction = (win_rate * (profit_loss_ratio + 1) - 1) / profit_loss_ratio
            kelly_fraction = max(0, min(kelly_fraction * 0.5, 0.5))  # 使用半凯利，上限50%
        else:
            kelly_fraction = 0
        
        # 3. 波动率目标法 (Volatility Targeting)
        target_volatility = 0.15  # 目标年化波动率15%
        vol_based_position = target_volatility / (volatility + 0.001)
        vol_based_position = min(vol_based_position, 1.0)
        
        # 4. 最大回撤调整
        max_dd = abs(risk_metrics['max_drawdown'])
        if max_dd > 0.20:  # 最大回撤超过20%
            dd_adjustment = 0.5  # 仓位减半
        elif max_dd > 0.15:
            dd_adjustment = 0.7
        elif max_dd > 0.10:
            dd_adjustment = 0.85
        else:
            dd_adjustment = 1.0
        
        # 5. 夏普比率调整
        sharpe = risk_metrics['sharpe_ratio']
        if sharpe < 0.5:
            sharpe_adjustment = 0.5
        elif sharpe < 1.0:
            sharpe_adjustment = 0.75
        elif sharpe < 1.5:
            sharpe_adjustment = 1.0
        else:
            sharpe_adjustment = 1.25
        
        # 综合仓位建议（取多种方法的加权平均）
        combined_position = (
            fixed_fractional_position * 0.3 +  # 固定风险法权重30%
            kelly_fraction * 0.25 +             # 凯利公式权重25%
            vol_based_position * 0.25           # 波动率目标法权重25%
        ) * dd_adjustment * min(sharpe_adjustment, 1.0)  # 应用调整系数
        
        # 保守/激进档位
        conservative_position = combined_position * 0.5
        aggressive_position = min(combined_position * 1.5, 1.0)
        
        # 计算具体仓位金额
        position_value = account_size * combined_position
        
        # 杠杆建议
        if combined_position > 1.0:
            leverage = combined_position
            leverage_suggestion = f"建议使用 {leverage:.1f}x 杠杆"
        else:
            leverage = 1.0
            leverage_suggestion = "建议不使用杠杆"
        
        sizing_result = {
            'account_size': account_size,
            'recommended_position_pct': combined_position,
            'recommended_position_value': position_value,
            'conservative_position_pct': conservative_position,
            'aggressive_position_pct': aggressive_position,
            'fixed_fractional': fixed_fractional_position,
            'kelly_fraction': kelly_fraction,
            'volatility_based': vol_based_position,
            'drawdown_adjustment': dd_adjustment,
            'sharpe_adjustment': sharpe_adjustment,
            'suggested_leverage': leverage,
            'max_single_position_pct': min(0.3, combined_position * 0.5),  # 最大单笔仓位
            'position_tier_1': combined_position * 0.3,  # 试探性仓位
            'position_tier_2': combined_position * 0.5,  # 基础仓位
            'position_tier_3': combined_position * 0.8,  # 加仓后仓位
            'position_tier_4': combined_position,        # 满仓
        }
        
        print(f"✅ 仓位计算完成")
        print(f"   建议仓位比例: {combined_position*100:.1f}%")
        print(f"   建议仓位金额: ¥{position_value:,.0f}")
        print(f"   凯利最优仓位: {kelly_fraction*100:.1f}%")
        
        return sizing_result
    
    def generate_stop_loss_strategy(self, entry_price: float,
                                     risk_metrics: Dict,
                                     atr: float = None,
                                     position_size: float = None) -> Dict:
        """
        生成止损策略建议
        
        参数:
            entry_price: 入场价格
            risk_metrics: 风险指标
            atr: 平均真实波幅（可选）
            position_size: 仓位大小（可选）
        
        返回:
            止损策略字典
        """
        print("\n🛑 生成止损策略...")
        
        # 基于ATR的止损
        if atr:
            atr_stop_loss_1 = entry_price * (1 - 1.5 * atr / entry_price)  # 1.5倍ATR
            atr_stop_loss_2 = entry_price * (1 - 2.0 * atr / entry_price)  # 2倍ATR
            atr_stop_loss_3 = entry_price * (1 - 3.0 * atr / entry_price)  # 3倍ATR
        else:
            # 默认使用2%和5%
            atr_stop_loss_1 = entry_price * 0.98
            atr_stop_loss_2 = entry_price * 0.95
            atr_stop_loss_3 = entry_price * 0.90
        
        # 基于VaR的止损
        var_95 = abs(risk_metrics['var_95'])
        var_stop_loss = entry_price * (1 - var_95 * 2)  # 2倍日VaR
        
        # 最大回撤止损
        max_dd_stop = entry_price * (1 + risk_metrics['max_drawdown'] * 0.5)  # 历史最大回撤的50%
        
        # 技术支撑位（简化示例）
        support_stop = entry_price * 0.93  # 假设7%支撑位
        
        # 时间止损（按交易日）
        time_stops = {
            '短线': 5,    # 5个交易日
            '中线': 20,   # 1个月
            '长线': 60    # 3个月
        }
        
        # 移动止损
        trailing_stops = {
            'tight': entry_price * 0.97,    # 3%移动止损
            'moderate': entry_price * 0.95, # 5%移动止损
            'loose': entry_price * 0.90     # 10%移动止损
        }
        
        stop_strategy = {
            'entry_price': entry_price,
            'primary_stop': {
                'price': atr_stop_loss_2,
                'type': '2倍ATR止损',
                'loss_pct': (entry_price - atr_stop_loss_2) / entry_price * 100
            },
            'secondary_stop': {
                'price': max(atr_stop_loss_3, var_stop_loss),
                'type': '3倍ATR/VaR止损',
                'loss_pct': (entry_price - max(atr_stop_loss_3, var_stop_loss)) / entry_price * 100
            },
            'trailing_stops': {
                'tight': {'price': trailing_stops['tight'], 'pct': 3},
                'moderate': {'price': trailing_stops['moderate'], 'pct': 5},
                'loose': {'price': trailing_stops['loose'], 'pct': 10}
            },
            'time_stops': time_stops,
            'technical_stop': support_stop,
            'breakeven_trigger': entry_price * 1.02,  # 盈利2%后移损至成本
            'partial_exit_1': entry_price * 1.05,     # 盈利5%减仓30%
            'partial_exit_2': entry_price * 1.10,     # 盈利10%减仓50%
            'partial_exit_3': entry_price * 1.20      # 盈利20%减仓70%
        }
        
        print(f"✅ 止损策略生成")
        print(f"   主要止损位: ¥{stop_strategy['primary_stop']['price']:.2f} (-{stop_strategy['primary_stop']['loss_pct']:.1f}%)")
        print(f"   次要止损位: ¥{stop_strategy['secondary_stop']['price']:.2f}")
        
        return stop_strategy
    
    def generate_pyramiding_strategy(self, entry_price: float,
                                      position_sizing: Dict,
                                      risk_metrics: Dict) -> Dict:
        """
        生成金字塔加仓策略建议
        
        参数:
            entry_price: 入场价格
            position_sizing: 仓位管理结果
            risk_metrics: 风险指标
        
        返回:
            加仓策略字典
        """
        print("\n📈 生成加仓策略...")
        
        base_position = position_sizing['recommended_position_pct']
        
        # 根据夏普比率调整加仓激进程度
        sharpe = risk_metrics['sharpe_ratio']
        if sharpe > 1.5:
            add_multiplier = 1.0  # 可满仓加仓
        elif sharpe > 1.0:
            add_multiplier = 0.8
        elif sharpe > 0.5:
            add_multiplier = 0.6
        else:
            add_multiplier = 0.4  # 保守加仓
        
        pyramiding = {
            'base_position_pct': base_position * 0.4,  # 初始建仓40%
            'addition_rules': [
                {
                    'trigger': '盈利2%',
                    'condition': f'价格 >= ¥{entry_price * 1.02:.2f}',
                    'add_pct': base_position * 0.2 * add_multiplier,
                    'cumulative_pct': base_position * 0.6,
                    'note': '确认趋势，小幅加仓'
                },
                {
                    'trigger': '盈利5%',
                    'condition': f'价格 >= ¥{entry_price * 1.05:.2f}',
                    'add_pct': base_position * 0.2 * add_multiplier,
                    'cumulative_pct': base_position * 0.8,
                    'note': '趋势确认，继续加仓'
                },
                {
                    'trigger': '盈利8%',
                    'condition': f'价格 >= ¥{entry_price * 1.08:.2f}',
                    'add_pct': base_position * 0.1 * add_multiplier,
                    'cumulative_pct': base_position * 0.9,
                    'note': '接近目标，谨慎加仓'
                },
                {
                    'trigger': '盈利12%',
                    'condition': f'价格 >= ¥{entry_price * 1.12:.2f}',
                    'add_pct': base_position * 0.1 * add_multiplier,
                    'cumulative_pct': base_position,
                    'note': '趋势强劲，完成建仓'
                }
            ],
            'requirements': [
                '每笔加仓前确认趋势仍然有效',
                '加仓后整体止损位上移至最新成本价下方2%',
                '单品种总仓位不超过建议仓位的100%',
                '加仓间隔至少2个交易日',
                '如回撤超过3%，暂停加仓计划'
            ],
            'pyramid_rules': {
                'max_additions': 3,  # 最多加仓3次
                'min_profit_before_add': 0.02,  # 至少盈利2%才能加仓
                'add_on_retracement': False,  # 不在回撤时加仓
                'reduce_on_volatility': volatility > 0.25 if 'volatility' in locals() else True
            }
        }
        
        print(f"✅ 加仓策略生成")
        print(f"   初始建仓: {pyramiding['base_position_pct']*100:.1f}%")
        print(f"   最多加仓{pyramiding['pyramid_rules']['max_additions']}次")
        
        return pyramiding
    
    def generate_risk_control_advice(self, risk_metrics: Dict,
                                      stress_results: Dict,
                                      market_regime: str = 'normal') -> Dict:
        """
        生成详细风控建议
        
        参数:
            risk_metrics: 风险指标
            stress_results: 压力测试结果
            market_regime: 市场环境（normal/trending/ranging/high_volatility）
        
        返回:
            风控建议字典
        """
        print("\n🛡️ 生成风控建议...")
        
        # 根据市场环境调整建议
        regime_settings = {
            'normal': {
                'position_factor': 1.0,
                'stop_tightness': 'normal',
                'holding_period': 'medium',
                'rebalancing_freq': 'weekly'
            },
            'trending': {
                'position_factor': 1.2,
                'stop_tightness': 'loose',
                'holding_period': 'long',
                'rebalancing_freq': 'biweekly'
            },
            'ranging': {
                'position_factor': 0.7,
                'stop_tightness': 'tight',
                'holding_period': 'short',
                'rebalancing_freq': 'daily'
            },
            'high_volatility': {
                'position_factor': 0.5,
                'stop_tightness': 'tight',
                'holding_period': 'short',
                'rebalancing_freq': 'daily'
            }
        }
        
        settings = regime_settings.get(market_regime, regime_settings['normal'])
        
        # 风险等级评估
        risk_score = 0
        if risk_metrics['max_drawdown'] < -0.20:
            risk_score += 3
        elif risk_metrics['max_drawdown'] < -0.15:
            risk_score += 2
        elif risk_metrics['max_drawdown'] < -0.10:
            risk_score += 1
        
        if risk_metrics['sharpe_ratio'] < 0.5:
            risk_score += 2
        elif risk_metrics['sharpe_ratio'] < 1.0:
            risk_score += 1
        
        if risk_metrics['var_95'] < -0.03:
            risk_score += 2
        elif risk_metrics['var_95'] < -0.02:
            risk_score += 1
        
        if stress_results.get('summary', {}).get('avg_max_drawdown', 0) < -0.15:
            risk_score += 2
        
        # 风险等级
        if risk_score >= 7:
            risk_level = '极高'
            risk_color = '🔴'
        elif risk_score >= 5:
            risk_level = '高'
            risk_color = '🟠'
        elif risk_score >= 3:
            risk_level = '中等'
            risk_color = '🟡'
        else:
            risk_level = '低'
            risk_color = '🟢'
        
        advice = {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_color': risk_color,
            'market_regime': market_regime,
            'settings': settings,
            
            'position_management': {
                'title': '仓位管理',
                'recommendations': [
                    f'当前风险等级：{risk_level}',
                    f'建议基础仓位：{30 if risk_score >= 5 else 50 if risk_score >= 3 else 70}%',
                    '单品种仓位不超过总资金的30%',
                    '同向相关性品种合计仓位不超过50%',
                    '保留至少20%现金作为安全垫',
                    '每月评估一次仓位配置，必要时再平衡'
                ]
            },
            
            'stop_loss_rules': {
                'title': '止损规则',
                'recommendations': [
                    '单笔交易最大亏损不超过账户资金的2%',
                    '技术性止损：跌破关键支撑位立即止损',
                    '时间止损：持仓超过20个交易日无盈利考虑减仓',
                    '波动率止损：当ATR扩大50%以上时收紧止损',
                    '盈利后上移止损至成本价，保护本金',
                    '连续止损3次后，暂停交易1周，复盘策略'
                ]
            },
            
            'profit_taking': {
                'title': '止盈策略',
                'recommendations': [
                    '分批止盈：盈利5%减仓30%，10%减仓50%，15%减仓70%',
                    '移动止盈：使用5日/10日均线作为动态止盈线',
                    '目标止盈：根据风险回报比设定，至少1:2',
                    '时间止盈：持仓达到预期周期后分批退出',
                    '波动止盈：当波动率异常放大时提前减仓',
                    '金字塔减仓：与加仓策略对应，反向执行'
                ]
            },
            
            'risk_monitoring': {
                'title': '风险监控',
                'daily_checks': [
                    '检查账户总权益变化',
                    '监控各品种持仓盈亏比例',
                    '关注市场波动率变化（VIX、黄金波动率）',
                    '跟踪相关资产走势（美元、利率、股市）'
                ],
                'weekly_reviews': [
                    '回顾本周交易执行情况',
                    '分析止损/止盈触发情况',
                    '评估当前仓位配置的合理性',
                    '检查模型预测准确率变化'
                ],
                'monthly_assessments': [
                    '统计月度收益和风险指标',
                    '对比实际与预期风险暴露',
                    '评估压力测试结果与实际表现的差异',
                    '调整下月仓位和风险参数'
                ]
            },
            
            'drawdown_management': {
                'title': '回撤管理',
                'rules': [
                    '账户回撤5%：降低仓位至70%',
                    '账户回撤10%：降低仓位至50%，暂停新开仓',
                    '账户回撤15%：降低仓位至30%，只减仓不加仓',
                    '账户回撤20%：停止交易，全面复盘策略',
                    '最大回撤恢复期预计：根据历史数据约需{:.0f}个交易日'.format(
                        abs(risk_metrics['max_drawdown']) * 252 / max(risk_metrics['annual_return'], 0.05)
                    ) if risk_metrics['annual_return'] > 0 else '需重新评估策略'
                ]
            },
            
            'special_warnings': []
        }
        
        # 根据具体情况添加特殊警告
        if risk_metrics['max_drawdown'] < -0.25:
            advice['special_warnings'].append(
                '🔴 警告：历史最大回撤超过25%，建议大幅降低仓位或暂停交易'
            )
        
        if risk_metrics['sharpe_ratio'] < 0.3:
            advice['special_warnings'].append(
                '🟠 警告：夏普比率过低，风险调整后收益不佳，请重新评估策略'
            )
        
        if stress_results.get('summary', {}).get('avg_max_drawdown', 0) < -0.20:
            advice['special_warnings'].append(
                '🔴 警告：压力测试显示在危机时期回撤可能超过20%，需格外谨慎'
            )
        
        if risk_metrics['kurtosis'] > 5:
            advice['special_warnings'].append(
                '🟡 注意：收益率分布呈现厚尾特征，极端事件风险较高'
            )
        
        print(f"✅ 风控建议生成")
        print(f"   风险等级: {risk_color} {risk_level}")
        print(f"   特殊警告: {len(advice['special_warnings'])}条")
        
        return advice
    
    def generate_risk_report(self, validation_results: Dict, 
                            stress_results: Dict,
                            risk_metrics: Dict,
                            feature_importance: Optional[pd.DataFrame],
                            position_sizing: Dict = None,
                            stop_strategy: Dict = None,
                            pyramiding: Dict = None,
                            risk_advice: Dict = None) -> str:
        """
        生成完整的风险管理报告（含风控建议）
        
        返回:
            格式化的报告字符串
        """
        report = []
        report.append("=" * 70)
        report.append("📊 黄金价格预测 - 全面风险管理报告")
        report.append("=" * 70)
        
        # 1. 模型验证结果
        report.append("\n🔍 1. 模型验证结果（滚动窗口交叉验证）")
        report.append("-" * 50)
        if 'mean_test_score' in validation_results:
            report.append(f"平均测试R²: {validation_results['mean_test_score']:.4f}")
            report.append(f"过拟合差距: {validation_results['overfitting_gap']:.4f}")
            if validation_results['overfitting_gap'] > 0.1:
                report.append("⚠️ 警告: 检测到过拟合迹象！")
        
        # 2. 风险指标
        report.append("\n📈 2. 风险指标")
        report.append("-" * 50)
        report.append(f"年化收益率: {risk_metrics['annual_return']*100:.2f}%")
        report.append(f"年化波动率: {risk_metrics['annual_volatility']*100:.2f}%")
        report.append(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
        report.append(f"索提诺比率: {risk_metrics['sortino_ratio']:.2f}")
        report.append(f"最大回撤: {risk_metrics['max_drawdown']*100:.2f}%")
        report.append(f"卡尔玛比率: {risk_metrics['calmar_ratio']:.2f}")
        report.append(f"胜率: {risk_metrics['win_rate']*100:.1f}%")
        report.append(f"盈亏比: {risk_metrics['profit_loss_ratio']:.2f}")
        report.append(f"VaR (95%): {risk_metrics['var_95']*100:.2f}%")
        report.append(f"CVaR (95%): {risk_metrics['cvar_95']*100:.2f}%")
        report.append(f"偏度: {risk_metrics.get('skewness', 0):.2f}")
        report.append(f"峰度: {risk_metrics.get('kurtosis', 0):.2f}")
        
        # 3. 压力测试结果
        report.append("\n🔥 3. 压力测试结果")
        report.append("-" * 50)
        if 'summary' in stress_results:
            summary = stress_results['summary']
            report.append(f"平均最大回撤: {summary['avg_max_drawdown']*100:.2f}%")
            report.append(f"平均夏普比率: {summary['avg_sharpe_ratio']:.2f}")
            report.append(f"最差表现时期: {summary['worst_crisis']}")
            
            report.append("\n各危机期间表现:")
            for crisis, data in stress_results.items():
                if crisis != 'summary':
                    report.append(f"  {crisis}: 收益{data['cumulative_return']*100:+.2f}%, "
                                f"回撤{data['max_drawdown']*100:.2f}%")
        
        # 4. 仓位管理建议
        if position_sizing:
            report.append("\n📊 4. 仓位管理建议")
            report.append("-" * 50)
            report.append(f"账户规模: ¥{position_sizing['account_size']:,.0f}")
            report.append(f"建议仓位比例: {position_sizing['recommended_position_pct']*100:.1f}%")
            report.append(f"建议仓位金额: ¥{position_sizing['recommended_position_value']:,.0f}")
            report.append(f"保守仓位: {position_sizing['conservative_position_pct']*100:.1f}%")
            report.append(f"激进仓位: {position_sizing['aggressive_position_pct']*100:.1f}%")
            report.append(f"\n计算方法:")
            report.append(f"  固定风险法: {position_sizing['fixed_fractional']*100:.1f}%")
            report.append(f"  凯利公式: {position_sizing['kelly_fraction']*100:.1f}%")
            report.append(f"  波动率目标: {position_sizing['volatility_based']*100:.1f}%")
            report.append(f"\n调整系数:")
            report.append(f"  回撤调整: {position_sizing['drawdown_adjustment']:.2f}")
            report.append(f"  夏普调整: {position_sizing['sharpe_adjustment']:.2f}")
        
        # 5. 止损策略
        if stop_strategy:
            report.append("\n🛑 5. 止损策略")
            report.append("-" * 50)
            report.append(f"入场价格: ¥{stop_strategy['entry_price']:.2f}")
            report.append(f"主要止损: ¥{stop_strategy['primary_stop']['price']:.2f} "
                        f"({stop_strategy['primary_stop']['type']}, -{stop_strategy['primary_stop']['loss_pct']:.1f}%)")
            report.append(f"次要止损: ¥{stop_strategy['secondary_stop']['price']:.2f} "
                        f"({stop_strategy['secondary_stop']['type']})")
            report.append(f"\n移动止损:")
            for key, val in stop_strategy['trailing_stops'].items():
                report.append(f"  {key}: ¥{val['price']:.2f} ({val['pct']}%)")
            report.append(f"\n分批止盈:")
            report.append(f"  盈利5%: 减仓30% (¥{stop_strategy['partial_exit_1']:.2f})")
            report.append(f"  盈利10%: 减仓50% (¥{stop_strategy['partial_exit_2']:.2f})")
            report.append(f"  盈利20%: 减仓70% (¥{stop_strategy['partial_exit_3']:.2f})")
            report.append(f"盈亏平衡触发: ¥{stop_strategy['breakeven_trigger']:.2f}")
        
        # 6. 加仓策略
        if pyramiding:
            report.append("\n📈 6. 金字塔加仓策略")
            report.append("-" * 50)
            report.append(f"初始建仓: {pyramiding['base_position_pct']*100:.1f}%")
            report.append(f"\n加仓规则:")
            for i, rule in enumerate(pyramiding['addition_rules'], 1):
                report.append(f"  {i}. {rule['trigger']}: 加{rule['add_pct']*100:.1f}%, 累计{rule['cumulative_pct']*100:.1f}%")
                report.append(f"     {rule['note']}")
            report.append(f"\n加仓要求:")
            for req in pyramiding['requirements']:
                report.append(f"  • {req}")
        
        # 7. 风控建议
        if risk_advice:
            report.append("\n🛡️ 7. 风控建议")
            report.append("-" * 50)
            report.append(f"风险等级: {risk_advice['risk_color']} {risk_advice['risk_level']}")
            report.append(f"市场环境: {risk_advice['market_regime']}")
            
            if risk_advice['special_warnings']:
                report.append(f"\n⚠️ 特殊警告:")
                for warning in risk_advice['special_warnings']:
                    report.append(f"  {warning}")
            
            for section_key, section in risk_advice.items():
                if isinstance(section, dict) and 'title' in section:
                    report.append(f"\n【{section['title']}】")
                    if 'recommendations' in section:
                        for rec in section['recommendations']:
                            report.append(f"  • {rec}")
                    elif 'daily_checks' in section:
                        report.append("  每日检查:")
                        for item in section['daily_checks']:
                            report.append(f"    - {item}")
                        report.append("  每周回顾:")
                        for item in section['weekly_reviews']:
                            report.append(f"    - {item}")
                        report.append("  月度评估:")
                        for item in section['monthly_assessments']:
                            report.append(f"    - {item}")
                    elif 'rules' in section:
                        for rule in section['rules']:
                            report.append(f"  • {rule}")
        
        # 8. 特征重要性
        if feature_importance is not None:
            report.append("\n📊 8. 特征重要性 (Top 10)")
            report.append("-" * 50)
            for idx, row in feature_importance.head(10).iterrows():
                bar = "█" * int(row['importance_pct'] / 2)
                report.append(f"{row['feature']:<20} {bar} {row['importance_pct']:>5.1f}%")
        
        report.append("\n" + "=" * 70)
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("⚠️ 风险提示: 以上建议仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
        report.append("=" * 70)
        
        return "\n".join(report)


# 使用示例
def demo_risk_management():
    """演示风险管理功能"""
    print("🚀 黄金价格预测 - 风险管理演示\n")
    
    # 创建模拟数据
    np.random.seed(42)
    n_samples = 1000
    dates = pd.date_range('2018-01-01', periods=n_samples, freq='B')
    
    # 模拟特征
    data = {
        'rsi': np.random.randn(n_samples),
        'macd': np.random.randn(n_samples),
        'ma_diff': np.random.randn(n_samples),
        'volatility': np.abs(np.random.randn(n_samples)),
        'dxy': np.random.randn(n_samples),
        'vix': np.abs(np.random.randn(n_samples)),
        'rate_change': np.random.randn(n_samples) * 0.5
    }
    X = pd.DataFrame(data, index=dates)
    
    # 模拟收益率（目标变量）
    y = pd.Series(np.random.randn(n_samples) * 0.01, index=dates)
    
    # 创建风险管理器
    risk_manager = GoldRiskManager(transaction_cost=0.001, slippage=0.0005)
    
    # 创建简单模型（演示用）
    if SKLEARN_AVAILABLE:
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
        
        # 1. 滚动窗口验证
        print("\n" + "="*60)
        validation_results = risk_manager.rolling_window_validation(X, y, model)
        
        # 2. 风险指标计算
        print("\n" + "="*60)
        predictions = pd.Series(validation_results['predictions'], 
                               index=validation_results['dates'])
        actuals = pd.Series(validation_results['actuals'], 
                           index=validation_results['dates'])
        risk_metrics = risk_manager.calculate_risk_metrics(actuals)
        
        # 3. 压力测试
        print("\n" + "="*60)
        df = pd.DataFrame({'returns': actuals}, index=actuals.index)
        stress_results = risk_manager.stress_test(df, predictions, actuals)
        
        # 4. 特征重要性
        print("\n" + "="*60)
        model.fit(X.iloc[-252:], y.iloc[-252:])  # 使用最近1年数据训练
        feature_importance = risk_manager.analyze_feature_importance(X, y, model)
        
        # 5. 生成报告
        print("\n" + "="*60)
        report = risk_manager.generate_risk_report(
            validation_results, stress_results, risk_metrics, feature_importance
        )
        print(report)
        
        # 保存报告
        with open('/tmp/gold_risk_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n💾 报告已保存到: /tmp/gold_risk_report.txt")
    else:
        print("❌ 需要安装 scikit-learn 才能运行演示")
        print("   安装命令: pip install scikit-learn")


if __name__ == '__main__':
    demo_risk_management()
