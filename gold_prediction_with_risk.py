#!/usr/bin/env python3
"""
黄金价格预测 - 集成风险管理模块
结合原有预测系统与风险管理的完整解决方案
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 导入风险管理模块
from gold_risk_management import GoldRiskManager

# 尝试导入预测相关库
try:
    from gold_macro_predictor import GoldMacroPredictor
    from gold_app import MacroFactorCollector
    PREDICTOR_AVAILABLE = True
except ImportError:
    PREDICTOR_AVAILABLE = False
    print("⚠️ 原有预测模块导入失败，将使用简化版本")


try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn 未安装，部分功能受限")


class GoldPredictionWithRisk:
    """
    带风险管理的黄金价格预测系统
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        初始化预测系统
        
        参数:
            risk_free_rate: 无风险利率（默认2%）
        """
        self.risk_manager = GoldRiskManager(
            transaction_cost=0.001,  # 0.1%交易成本
            slippage=0.0005          # 0.05%滑点
        )
        self.risk_free_rate = risk_free_rate
        self.models = {}
        self.validation_results = {}
        self.stress_results = {}
        self.risk_metrics = {}
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        准备特征数据 - 防范幸存者偏差
        确保包含完整周期的数据
        """
        print("📊 准备特征数据...")
        
        features = pd.DataFrame(index=df.index)
        
        # 技术指标
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        features['macd'] = exp1 - exp2
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        
        # 移动平均线差异
        features['ma5'] = df['close'].rolling(window=5).mean()
        features['ma20'] = df['close'].rolling(window=20).mean()
        features['ma_diff'] = (features['ma5'] - features['ma20']) / features['ma20']
        
        # 波动率
        features['volatility'] = df['close'].pct_change().rolling(window=20).std()
        
        # 价格动量
        features['momentum_5'] = df['close'].pct_change(5)
        features['momentum_20'] = df['close'].pct_change(20)
        
        # 成交量特征
        features['volume_ma'] = df['volume'].rolling(window=20).mean()
        features['volume_ratio'] = df['volume'] / features['volume_ma']
        
        # 目标变量 - 未来5日收益率
        features['target'] = df['close'].pct_change(5).shift(-5)
        
        # 删除缺失值
        features = features.dropna()
        
        print(f"✅ 特征准备完成: {len(features)} 条记录")
        print(f"   时间跨度: {features.index[0]} ~ {features.index[-1]}")
        
        # 检查数据完整性
        start_year = features.index[0].year
        end_year = features.index[-1].year
        print(f"   包含年份: {start_year} - {end_year}")
        
        # 提示是否包含关键危机时期
        crisis_years = [2008, 2009, 2010, 2011, 2015, 2020, 2022]
        covered_crisis = [y for y in crisis_years if start_year <= y <= end_year]
        if covered_crisis:
            print(f"   ✅ 包含危机年份数据: {covered_crisis}")
        else:
            print(f"   ⚠️ 警告: 数据可能缺少危机时期数据")
        
        return features
    
    def train_with_validation(self, features: pd.DataFrame, 
                             model_type: str = 'ensemble') -> Dict:
        """
        训练模型并进行滚动窗口验证
        """
        print("\n" + "="*60)
        print("🚀 开始训练模型并验证...")
        print("="*60)
        
        # 分离特征和目标
        X = features.drop('target', axis=1)
        y = features['target']
        
        if not SKLEARN_AVAILABLE:
            print("❌ 需要安装 scikit-learn")
            return {}
        
        # 创建模型
        if model_type == 'rf':
            model = RandomForestRegressor(
                n_estimators=100, 
                max_depth=5,
                min_samples_split=20,
                random_state=42
            )
        elif model_type == 'gb':
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )
        else:  # ensemble
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        
        # 1. 滚动窗口交叉验证
        print("\n🔍 步骤1: 滚动窗口交叉验证（防范过拟合）")
        self.validation_results = self.risk_manager.rolling_window_validation(
            X, y, model, 
            window_size=252,  # 1年训练窗口
            step_size=21      # 每月滚动一次
        )
        
        # 检查过拟合
        if self.validation_results.get('overfitting_gap', 0) > 0.15:
            print("\n⚠️ 检测到过拟合，调整模型参数...")
            model = RandomForestRegressor(
                n_estimators=50,
                max_depth=3,
                min_samples_split=30,
                random_state=42
            )
            # 重新验证
            self.validation_results = self.risk_manager.rolling_window_validation(
                X, y, model, window_size=252, step_size=21
            )
        
        # 2. 在全量数据上训练最终模型
        print("\n🔧 步骤2: 训练最终模型")
        model.fit(X, y)
        self.models['main'] = model
        
        # 3. 计算风险指标
        print("\n📈 步骤3: 计算风险指标")
        predictions = pd.Series(
            self.validation_results['predictions'],
            index=self.validation_results['dates']
        )
        actuals = pd.Series(
            self.validation_results['actuals'],
            index=self.validation_results['dates']
        )
        
        # 应用交易成本
        net_returns = self.risk_manager.apply_transaction_costs(
            actuals, turnover_rate=0.5
        )
        
        self.risk_metrics = self.risk_manager.calculate_risk_metrics(
            net_returns, risk_free_rate=self.risk_free_rate
        )
        
        # 4. 压力测试
        print("\n🔥 步骤4: 执行压力测试")
        df_test = pd.DataFrame({'returns': actuals}, index=actuals.index)
        self.stress_results = self.risk_manager.stress_test(
            df_test, predictions, actuals
        )
        
        # 5. 特征重要性分析
        print("\n📊 步骤5: 特征重要性分析")
        self.feature_importance = self.risk_manager.analyze_feature_importance(
            X, y, model
        )
        
        # 6. 过拟合防御体系检测
        print("\n🔮 步骤6: 过拟合防御体系检测")
        self.defense_results = self.risk_manager.overfitting_defense_system(
            X, y, model, n_splits=5
        )
        
        # 7. 模型失效预警
        print("\n🔮 步骤7: 模型失效预警系统")
        # 使用验证集结果进行失效检测
        if self.validation_results.get('predictions'):
            predictions_series = pd.Series(
                self.validation_results['predictions'],
                index=self.validation_results['dates']
            )
            actuals_series = pd.Series(
                self.validation_results['actuals'],
                index=self.validation_results['dates']
            )
            
            # 构建特征重要性历史（简化）
            feature_history = []
            if self.feature_importance is not None:
                importance_dict = dict(zip(
                    self.feature_importance['feature'],
                    self.feature_importance['importance_pct'] / 100
                ))
                feature_history.append(importance_dict)
            
            self.failure_alerts = self.risk_manager.model_failure_detection(
                actuals_series.iloc[-100:],
                predictions_series.iloc[-100:],
                feature_history,
                actuals_series.iloc[-100:]
            )
        else:
            self.failure_alerts = {'status': 'UNKNOWN', 'warnings': []}
        
        # 8. 生成预测信号
        print("\n🔮 步骤8: 生成当前预测信号")
        latest_features = X.iloc[-1:]
        current_prediction = model.predict(latest_features)[0]
        
        # 计算置信度（基于历史预测误差）
        prediction_errors = np.array(self.validation_results['actuals']) - np.array(self.validation_results['predictions'])
        mae = np.mean(np.abs(prediction_errors))
        confidence = max(0, 1 - mae / (np.std(actuals) + 1e-6))
        
        self.current_signal = {
            'predicted_return_5d': current_prediction,
            'confidence': confidence,
            'signal_strength': '强' if abs(current_prediction) > 0.02 else '中' if abs(current_prediction) > 0.01 else '弱',
            'direction': '看多' if current_prediction > 0 else '看空',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"\n📌 当前预测信号:")
        print(f"   方向: {self.current_signal['direction']}")
        print(f"   预测5日收益: {current_prediction*100:+.2f}%")
        print(f"   置信度: {confidence*100:.1f}%")
        print(f"   信号强度: {self.current_signal['signal_strength']}")
        
        return self.current_signal
    
    def get_trading_suggestion(self, current_price: float = None, 
                                  account_size: float = 1000000,
                                  market_regime: str = 'normal') -> str:
        """
        生成详细交易建议，包含完整风控方案
        
        参数:
            current_price: 当前价格（用于生成具体止损位）
            account_size: 账户规模
            market_regime: 市场环境
        """
        if not hasattr(self, 'current_signal'):
            return "❌ 请先运行模型训练"
        
        signal = self.current_signal
        risk = self.risk_metrics
        
        # 计算详细风控参数
        position_sizing = self.risk_manager.calculate_position_sizing(
            risk, account_size=account_size
        )
        
        # Kelly准则动态仓位
        kelly_position = self.risk_manager.kelly_position_sizing(
            win_rate=risk['win_rate'],
            profit_loss_ratio=risk['profit_loss_ratio'],
            account_size=account_size,
            kelly_fraction=0.25  # 使用1/4 Kelly
        )
        
        # 分层仓位架构
        hierarchical = self.risk_manager.hierarchical_position_structure(
            base_position=kelly_position['final_position_pct'],
            account_size=account_size,
            risk_budget=0.10
        )
        
        stop_strategy = None
        if current_price:
            stop_strategy = self.risk_manager.generate_stop_loss_strategy(
                current_price, risk
            )
        
        pyramiding = None
        if current_price:
            pyramiding = self.risk_manager.generate_pyramiding_strategy(
                current_price, position_sizing, risk
            )
        
        risk_advice = self.risk_manager.generate_risk_control_advice(
            risk, self.stress_results, market_regime
        )
        
        # 保存风控结果
        self.position_sizing = position_sizing
        self.stop_strategy = stop_strategy
        self.pyramiding = pyramiding
        self.risk_advice = risk_advice
        
        suggestion = []
        suggestion.append("="*70)
        suggestion.append("💡 黄金交易建议与风控方案")
        suggestion.append("="*70)
        
        # 预测信号
        suggestion.append("\n📊 【预测信号】")
        suggestion.append("-"*50)
        suggestion.append(f"预测方向: {signal['direction']}")
        suggestion.append(f"预测5日收益: {signal['predicted_return_5d']*100:+.2f}%")
        suggestion.append(f"信号强度: {signal['signal_strength']}")
        suggestion.append(f"置信度: {signal['confidence']*100:.1f}%")
        
        # 基于预测信号的交易方向
        suggestion.append("\n📈 【交易方向建议】")
        suggestion.append("-"*50)
        if signal['predicted_return_5d'] > 0.02 and signal['confidence'] > 0.5:
            suggestion.append("🟢 建议操作: 做多")
            suggestion.append(f"   理由: 模型预测5日上涨{signal['predicted_return_5d']*100:.2f}%，置信度{signal['confidence']*100:.1f}%")
        elif signal['predicted_return_5d'] < -0.02 and signal['confidence'] > 0.5:
            suggestion.append("🔴 建议操作: 做空/减仓")
            suggestion.append(f"   理由: 模型预测5日下跌{abs(signal['predicted_return_5d'])*100:.2f}%，置信度{signal['confidence']*100:.1f}%")
        else:
            suggestion.append("🟡 建议操作: 观望")
            suggestion.append(f"   理由: 信号不明确（预测{signal['predicted_return_5d']*100:+.2f}%，置信度{signal['confidence']*100:.1f}%）")
        
        # 仓位管理
        suggestion.append("\n📊 【仓位管理】")
        suggestion.append("-"*50)
        suggestion.append(f"账户规模: ¥{position_sizing['account_size']:,.0f}")
        suggestion.append(f"建议总仓位: {position_sizing['recommended_position_pct']*100:.1f}% "
                        f"(¥{position_sizing['recommended_position_value']:,.0f})")
        suggestion.append(f"保守仓位: {position_sizing['conservative_position_pct']*100:.1f}%")
        suggestion.append(f"激进仓位: {position_sizing['aggressive_position_pct']*100:.1f}%")
        suggestion.append(f"\n仓位计算方法:")
        suggestion.append(f"  • 固定风险法: {position_sizing['fixed_fractional']*100:.1f}%")
        suggestion.append(f"  • 凯利公式: {position_sizing['kelly_fraction']*100:.1f}%")
        suggestion.append(f"  • 波动率目标: {position_sizing['volatility_based']*100:.1f}%")
        suggestion.append(f"\n重要限制:")
        suggestion.append(f"  • 单品种最大仓位: {position_sizing['max_single_position_pct']*100:.1f}%")
        suggestion.append(f"  • 建议保留现金: 20%")
        
        # Kelly准则动态仓位
        suggestion.append("\n📈 【Kelly准则动态仓位】")
        suggestion.append("-"*50)
        suggestion.append(f"公式: f* = W - (1-W)/R")
        suggestion.append(f"  W(胜率): {kelly_position['win_rate']*100:.1f}%")
        suggestion.append(f"  R(盈亏比): {kelly_position['profit_loss_ratio']:.2f}")
        suggestion.append(f"Full Kelly: {kelly_position['full_kelly']*100:.1f}%")
        suggestion.append(f"使用Kelly分数: {kelly_position['kelly_fraction']*100:.0f}% (1/4 Kelly)")
        suggestion.append(f"实用Kelly仓位: {kelly_position['practical_kelly']*100:.1f}%")
        if kelly_position['adjustments']:
            suggestion.append(f"黄金特殊调整:")
            for adj in kelly_position['adjustments']:
                suggestion.append(f"  • {adj}")
        suggestion.append(f"最终Kelly仓位: {kelly_position['final_position_pct']*100:.1f}%")
        
        # 分层仓位架构
        suggestion.append("\n🏗️ 【分层仓位架构】")
        suggestion.append("-"*50)
        suggestion.append(f"总风险预算: {hierarchical['total_risk_budget']*100:.0f}%")
        suggestion.append(f"基础仓位: {hierarchical['base_position']*100:.1f}%")
        suggestion.append(f"\n分层配置:")
        suggestion.append(f"  ├─ 核心仓位(60%): {hierarchical['core_position']['pct']*100:.1f}% "
                        f"= ¥{hierarchical['core_position']['value']:,.0f}")
        suggestion.append(f"  │   └─ {hierarchical['core_position']['description']}")
        suggestion.append(f"  ├─ 对冲仓位(30%): {hierarchical['hedge_position']['pct']*100:.1f}% "
                        f"= ¥{hierarchical['hedge_position']['value']:,.0f}")
        suggestion.append(f"  │   └─ {hierarchical['hedge_position']['description']}")
        suggestion.append(f"  └─ 机动仓位(10%): {hierarchical['tactical_position']['pct']*100:.1f}% "
                        f"= ¥{hierarchical['tactical_position']['value']:,.0f}")
        suggestion.append(f"      └─ {hierarchical['tactical_position']['description']}")
        suggestion.append(f"\n风险限制:")
        suggestion.append(f"  • 单日最大损失限制: ¥{hierarchical['risk_limits']['max_daily_loss_value']:,.0f} (账户2%)")
        suggestion.append(f"  • 预估风险敞口(VaR 95%): ¥{hierarchical['risk_limits']['actual_risk_exposure']:,.0f}")
        
        # 止损策略
        if stop_strategy:
            suggestion.append("\n🛑 【止损策略】")
            suggestion.append("-"*50)
            suggestion.append(f"入场参考价: ¥{stop_strategy['entry_price']:.2f}")
            suggestion.append(f"\n主要止损位: ¥{stop_strategy['primary_stop']['price']:.2f}")
            suggestion.append(f"  类型: {stop_strategy['primary_stop']['type']}")
            suggestion.append(f"  最大亏损: {stop_strategy['primary_stop']['loss_pct']:.1f}%")
            suggestion.append(f"\n次要止损位: ¥{stop_strategy['secondary_stop']['price']:.2f}")
            suggestion.append(f"  类型: {stop_strategy['secondary_stop']['type']}")
            suggestion.append(f"\n移动止损建议:")
            for key, val in stop_strategy['trailing_stops'].items():
                suggestion.append(f"  • {key}: ¥{val['price']:.2f} (回撤{val['pct']}%触发)")
            suggestion.append(f"\n盈亏平衡触发: 盈利达¥{stop_strategy['breakeven_trigger']:.2f}后上移止损")
        
        # 加仓策略
        if pyramiding:
            suggestion.append("\n📈 【加仓策略（金字塔）】")
            suggestion.append("-"*50)
            suggestion.append(f"初始建仓: {pyramiding['base_position_pct']*100:.1f}%")
            suggestion.append(f"\n加仓计划:")
            for i, rule in enumerate(pyramiding['addition_rules'], 1):
                suggestion.append(f"  {i}. {rule['trigger']}")
                suggestion.append(f"     加仓: {rule['add_pct']*100:.1f}% | 累计: {rule['cumulative_pct']*100:.1f}%")
                suggestion.append(f"     条件: {rule['condition']}")
            suggestion.append(f"\n加仓纪律:")
            for req in pyramiding['requirements']:
                suggestion.append(f"  • {req}")
        
        # 止盈策略
        if stop_strategy:
            suggestion.append("\n💰 【止盈策略】")
            suggestion.append("-"*50)
            suggestion.append("分批止盈计划:")
            suggestion.append(f"  1. 盈利5% (¥{stop_strategy['partial_exit_1']:.2f}): 减仓30%")
            suggestion.append(f"  2. 盈利10% (¥{stop_strategy['partial_exit_2']:.2f}): 再减仓20% (累计50%)")
            suggestion.append(f"  3. 盈利20% (¥{stop_strategy['partial_exit_3']:.2f}): 再减仓20% (累计70%)")
            suggestion.append(f"\n移动止盈: 使用5日/10日均线作为动态止盈线")
            suggestion.append(f"时间止盈: 持仓超过20个交易日考虑逐步减仓")
        
        # 过拟合防御体系
        if hasattr(self, 'defense_results') and self.defense_results:
            suggestion.append("\n🛡️ 【过拟合防御体系】")
            suggestion.append("-"*50)
            defense = self.defense_results
            suggestion.append(f"整体状态: {defense['overall_status']}")
            
            if 'cross_validation' in defense['defense_layers']:
                cv = defense['defense_layers']['cross_validation']
                suggestion.append(f"交叉验证: 平均R²={cv.get('cv_mean', 0):.4f}, 最小R²={cv.get('cv_min', 0):.4f}")
            
            if 'monte_carlo' in defense['defense_layers']:
                mc = defense['defense_layers']['monte_carlo']
                suggestion.append(f"蒙特卡洛稳健性: {mc.get('robustness_rate', 0)*100:.1f}%")
            
            if 'walk_forward' in defense['defense_layers']:
                wf = defense['defense_layers']['walk_forward']
                suggestion.append(f"Walk-Forward: 周期数={wf.get('n_periods', 0)}, 最长低R²连续={wf.get('max_low_r2_streak', 0)}个月")
            
            if defense['critical_alerts']:
                suggestion.append(f"\n🔴 防御警报:")
                for alert in defense['critical_alerts']:
                    suggestion.append(f"  {alert}")
        
        # 模型失效预警
        if hasattr(self, 'failure_alerts') and self.failure_alerts:
            suggestion.append("\n⚠️ 【模型失效预警】")
            suggestion.append("-"*50)
            alerts = self.failure_alerts
            status_icons = {'NORMAL': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴'}
            suggestion.append(f"监控状态: {status_icons.get(alerts['status'], '⚪')} {alerts['status']}")
            
            if 'current_mape' in alerts.get('indicators', {}):
                suggestion.append(f"当前MAPE: {alerts['indicators']['current_mape']:.4f}")
            
            if 'dw_stat' in alerts.get('indicators', {}):
                suggestion.append(f"Durbin-Watson: {alerts['indicators']['dw_stat']:.4f}")
            
            if alerts['critical_alerts']:
                suggestion.append(f"\n🔴 关键预警:")
                for alert in alerts['critical_alerts']:
                    suggestion.append(f"  {alert}")
            
            if alerts['warnings']:
                suggestion.append(f"\n🟡 警告:")
                for warning in alerts['warnings']:
                    suggestion.append(f"  {warning}")
            
            if alerts['recommendations']:
                suggestion.append(f"\n💡 建议:")
                for rec in alerts['recommendations']:
                    suggestion.append(f"  {rec}")
        
        # 监控仪表盘
        suggestion.append("\n📊 【风控监控仪表盘】")
        suggestion.append("-"*50)
        
        # 获取模型状态
        model_status = 'NORMAL'
        if hasattr(self, 'failure_alerts'):
            model_status = self.failure_alerts.get('status', 'NORMAL')
        
        # 生成仪表盘
        dashboard = self.risk_manager.generate_risk_dashboard(
            model_status=model_status,
            current_position=kelly_position['final_position_pct'],
            today_var=risk.get('var_95', 0.018),
            gvz_index=18  # 假设值
        )
        suggestion.append(dashboard)
        
        # 风控等级与监控
        suggestion.append("\n🛡️ 【风控等级与监控】")
        suggestion.append("-"*50)
        suggestion.append(f"当前风险等级: {risk_advice['risk_color']} {risk_advice['risk_level']}")
        suggestion.append(f"市场环境: {market_regime}")
        
        if risk_advice['special_warnings']:
            suggestion.append(f"\n⚠️ 特殊警告:")
            for warning in risk_advice['special_warnings']:
                suggestion.append(f"  {warning}")
        
        suggestion.append(f"\n回撤管理规则:")
        for rule in risk_advice['drawdown_management']['rules']:
            suggestion.append(f"  • {rule}")
        
        # 风险提示
        suggestion.append("\n⚠️ 【关键风险提示】")
        suggestion.append("-"*50)
        suggestion.append(f"历史最大回撤: {risk['max_drawdown']*100:.2f}%")
        suggestion.append(f"夏普比率: {risk['sharpe_ratio']:.2f} {'(优秀)' if risk['sharpe_ratio'] > 1 else '(一般)' if risk['sharpe_ratio'] > 0.5 else '(较差)'}")
        suggestion.append(f"95% VaR: {risk['var_95']*100:.2f}% (单日最大可能亏损)")
        suggestion.append(f"95% CVaR: {risk['cvar_95']*100:.2f}% (极端情况下平均亏损)")
        
        # 每日检查清单
        suggestion.append("\n📋 【每日交易检查清单】")
        suggestion.append("-"*50)
        suggestion.append("  □ 检查账户总权益变化")
        suggestion.append("  □ 监控各持仓盈亏比例")
        suggestion.append("  □ 确认止损位是否仍然有效")
        suggestion.append("  □ 关注美元指数、VIX等关联指标")
        suggestion.append("  □ 检查是否触发加仓/减仓条件")
        suggestion.append("  □ 确认是否达到盈亏平衡点需移损")
        
        suggestion.append("\n" + "="*70)
        suggestion.append("⚠️ 免责声明: 以上建议基于历史数据模型，仅供参考，不构成投资建议。")
        suggestion.append("   金融市场有风险，投资需谨慎。请根据自身风险承受能力独立决策。")
        suggestion.append("="*70)
        
        return "\n".join(suggestion)
    
    def generate_full_report(self, current_price: float = None, 
                              account_size: float = 1000000,
                              market_regime: str = 'normal') -> str:
        """
        生成完整的风险管理报告（包含详细风控建议）
        
        参数:
            current_price: 当前价格
            account_size: 账户规模
            market_regime: 市场环境
        """
        # 计算详细风控参数
        position_sizing = self.risk_manager.calculate_position_sizing(
            self.risk_metrics, account_size=account_size
        )
        
        stop_strategy = None
        pyramiding = None
        if current_price:
            stop_strategy = self.risk_manager.generate_stop_loss_strategy(
                current_price, self.risk_metrics
            )
            pyramiding = self.risk_manager.generate_pyramiding_strategy(
                current_price, position_sizing, self.risk_metrics
            )
        
        risk_advice = self.risk_manager.generate_risk_control_advice(
            self.risk_metrics, self.stress_results, market_regime
        )
        
        # 保存风控结果
        self.position_sizing = position_sizing
        self.stop_strategy = stop_strategy
        self.pyramiding = pyramiding
        self.risk_advice = risk_advice
        
        return self.risk_manager.generate_risk_report(
            self.validation_results,
            self.stress_results,
            self.risk_metrics,
            self.feature_importance,
            position_sizing,
            stop_strategy,
            pyramiding,
            risk_advice
        )
    
    def save_report(self, filepath: str = None, current_price: float = None,
                   account_size: float = 1000000, market_regime: str = 'normal'):
        """
        保存完整报告到文件
        
        参数:
            filepath: 文件路径
            current_price: 当前价格
            account_size: 账户规模
            market_regime: 市场环境
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f'/tmp/gold_prediction_report_{timestamp}.txt'
        
        report = self.generate_full_report(current_price, account_size, market_regime)
        trading_suggestion = self.get_trading_suggestion(current_price, account_size, market_regime)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n")
            f.write("=" * 70)
            f.write("\n")
            f.write(trading_suggestion)
        
        print(f"\n💾 完整报告已保存到: {filepath}")
        return filepath


def run_full_prediction(account_size: float = 1000000, 
                         market_regime: str = 'normal'):
    """
    运行完整的预测流程，包含详细风控建议
    
    参数:
        account_size: 账户规模（默认100万）
        market_regime: 市场环境（normal/trending/ranging/high_volatility）
    """
    print("🚀 启动黄金价格预测（含全面风险管理）\n")
    
    # 创建预测系统
    predictor = GoldPredictionWithRisk(risk_free_rate=0.02)
    
    # 加载数据（这里使用模拟数据演示）
    print("📊 加载历史数据...")
    current_price = None
    try:
        import akshare as ak
        # 尝试获取真实数据
        df = ak.futures_zh_daily_sina(symbol='AU0')
        if df is not None and len(df) > 500:
            print(f"✅ 成功加载 {len(df)} 条历史数据")
            current_price = float(df['close'].iloc[-1])
            print(f"   当前价格: ¥{current_price:.2f}")
        else:
            raise Exception("数据不足")
    except Exception as e:
        print(f"⚠️ 使用模拟数据（{e}）")
        # 生成模拟数据
        np.random.seed(42)
        n_samples = 1000
        dates = pd.date_range('2018-01-01', periods=n_samples, freq='B')
        current_price = 500.0  # 模拟当前价格
        df = pd.DataFrame({
            'date': dates,
            'close': 350 + np.cumsum(np.random.randn(n_samples) * 2),
            'open': 350 + np.cumsum(np.random.randn(n_samples) * 2),
            'high': 355 + np.cumsum(np.random.randn(n_samples) * 2),
            'low': 345 + np.cumsum(np.random.randn(n_samples) * 2),
            'volume': np.random.randint(10000, 100000, n_samples)
        })
        df.set_index('date', inplace=True)
    
    # 准备特征
    features = predictor.prepare_features(df)
    
    if len(features) < 500:
        print("❌ 数据量不足，无法进行有效验证")
        return
    
    # 训练模型并进行风险管理
    signal = predictor.train_with_validation(features, model_type='ensemble')
    
    # 显示详细交易建议（包含完整风控方案）
    print("\n" + predictor.get_trading_suggestion(
        current_price=current_price,
        account_size=account_size,
        market_regime=market_regime
    ))
    
    # 保存完整报告
    predictor.save_report(
        current_price=current_price,
        account_size=account_size,
        market_regime=market_regime
    )
    
    print("\n" + "="*70)
    print("✅ 预测流程完成！已生成完整风控方案")
    print("="*70)
    
    return predictor


if __name__ == '__main__':
    predictor = run_full_prediction()
