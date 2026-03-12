"""
增强版铜价预测 - 集成四层宏观调整因子

使用流程：
1. 基础价格预测（技术分析模型）
2. 宏观因子调整（四层架构）
3. 风险调整后最终预测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# 导入原有模块
from copper_prediction import get_copper_data, calculate_indicators
from copper_risk_management import CopperRiskManager, CopperRiskDashboard
from copper_macro_factors import CopperMacroAdjustmentSystem, get_default_macro_data


class EnhancedCopperPredictor:
    """
    增强版铜价预测器
    
    整合：
    1. 技术分析基础预测
    2. 四层宏观因子调整
    3. 风险量化与置信区间
    """
    
    def __init__(self):
        self.macro_system = CopperMacroAdjustmentSystem()
        self.risk_dashboard = CopperRiskDashboard()
        self.forecast_horizon = 7  # 7天预测
        
    def predict(self, 
                macro_data: Optional[Dict] = None,
                use_macro_adjustment: bool = True,
                use_risk_management: bool = True) -> Dict:
        """
        执行完整预测流程
        
        Args:
            macro_data: 宏观经济数据，None则使用默认数据
            use_macro_adjustment: 是否使用宏观因子调整
            use_risk_management: 是否使用风险管理模块
            
        Returns:
            完整预测结果字典
        """
        print("=" * 70)
        print("🔶 增强版铜价预测系统")
        print("=" * 70)
        
        # 步骤1: 获取基础数据
        print("\n📊 步骤1: 获取铜期货数据...")
        df = get_copper_data()
        if df is None or df.empty:
            return {"error": "无法获取铜价数据"}
        
        df = calculate_indicators(df)
        current_price = df['Close'].iloc[-1]
        print(f"   当前铜价: {current_price:,.2f} 元/吨")
        
        # 步骤2: 基础价格预测
        print("\n📈 步骤2: 基础价格预测...")
        base_prediction = self._base_price_prediction(df)
        
        # 步骤3: 宏观因子调整
        macro_adjustment = None
        if use_macro_adjustment:
            print("\n🌍 步骤3: 四层宏观因子分析...")
            if macro_data is None:
                macro_data = get_default_macro_data()
            macro_adjustment = self.macro_system.calculate(macro_data)
            print(self.macro_system.get_summary(macro_adjustment))
        
        # 步骤4: 风险量化
        risk_metrics = None
        if use_risk_management:
            print("\n🛡️ 步骤4: 风险量化分析...")
            returns = df['Close'].pct_change().dropna().values
            
            # 计算基础风险指标
            risk_metrics = self.risk_dashboard.calculate_all_metrics(
                df, 
                {'base_model': base_prediction['point_forecast']}
            )
            
            # 添加预测区间
            feature_cols = ['Close', 'MA5', 'MA20', 'RSI', 'MACD', 'Volatility']
            risk_mgr = CopperRiskManager(confidence_level=0.95)
            
            df_clean = df.dropna()
            if len(df_clean) > 50:
                X = df_clean[feature_cols].values[:-self.forecast_horizon]
                y = df_clean['Close'].values[self.forecast_horizon:]
                
                train_size = int(len(X) * 0.8)
                X_train, X_cal = X[:train_size], X[train_size:]
                y_train, y_cal = y[:train_size], y[train_size:]
                
                risk_mgr.train_quantile_models(X_train, y_train)
                
                last_features = df_clean[feature_cols].values[-1:]
                prediction_result = risk_mgr.predict_with_uncertainty(last_features, method='quantile')
                
                risk_metrics['prediction_intervals'] = prediction_result
                print(f"   预测区间 (95%): [{prediction_result['lower_95'][0]:,.2f}, {prediction_result['upper_95'][0]:,.2f}]")
        
        # 步骤5: 综合最终预测
        print("\n🎯 步骤5: 生成最终预测...")
        final_prediction = self._generate_final_prediction(
            current_price,
            base_prediction,
            macro_adjustment,
            risk_metrics
        )
        
        # 组装结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'current_price': float(current_price),
            'forecast_horizon_days': self.forecast_horizon,
            'base_prediction': base_prediction,
            'macro_adjustment': macro_adjustment,
            'risk_metrics': risk_metrics,
            'final_prediction': final_prediction
        }
        
        # 打印摘要
        self._print_summary(result)
        
        return result
    
    def _base_price_prediction(self, df: pd.DataFrame) -> Dict:
        """基础价格预测（技术面）"""
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor
        
        df_clean = df.dropna()
        features = ['Close', 'MA5', 'MA20', 'RSI', 'MACD', 'Volatility']
        
        X = df_clean[features].values[:-self.forecast_horizon]
        y = df_clean['Close'].values[self.forecast_horizon:]
        
        # 简单线性模型
        lr = LinearRegression()
        lr.fit(X, y)
        
        # 随机森林模型
        rf = RandomForestRegressor(n_estimators=50, random_state=42)
        rf.fit(X, y)
        
        # 预测未来7天
        last_row = df_clean[features].values[-1:]
        
        lr_preds = []
        rf_preds = []
        last = last_row.copy()
        
        for _ in range(self.forecast_horizon):
            lr_pred = lr.predict(last)[0]
            rf_pred = rf.predict(last)[0]
            lr_preds.append(lr_pred)
            rf_preds.append(rf_pred)
            # 更新特征（简化处理）
            last[0][0] = (lr_pred + rf_pred) / 2
        
        # 集成预测
        ensemble_preds = [(l + r) / 2 for l, r in zip(lr_preds, rf_preds)]
        
        current_price = df['Close'].iloc[-1]
        predicted_change = (ensemble_preds[-1] - current_price) / current_price
        
        return {
            'method': 'ensemble_ml',
            'point_forecast': float(ensemble_preds[-1]),
            'forecast_path': [float(p) for p in ensemble_preds],
            'predicted_change_pct': float(predicted_change * 100),
            'direction': 'up' if predicted_change > 0 else 'down',
            'model_details': {
                'linear_reg_final': float(lr_preds[-1]),
                'random_forest_final': float(rf_preds[-1])
            }
        }
    
    def _generate_final_prediction(self,
                                    current_price: float,
                                    base_prediction: Dict,
                                    macro_adjustment: Optional[Dict],
                                    risk_metrics: Optional[Dict]) -> Dict:
        """生成最终预测结果"""
        
        base_forecast = base_prediction['point_forecast']
        
        # 应用宏观调整
        if macro_adjustment:
            adjustment_pct = macro_adjustment['adjustment']['price_adjustment_pct'] / 100
            macro_signal = macro_adjustment['signal']
            macro_score = macro_adjustment['composite_score']
        else:
            adjustment_pct = 0
            macro_signal = "未启用"
            macro_score = 0
        
        # 调整后的价格
        adjusted_price = base_forecast * (1 + adjustment_pct)
        
        # 风险调整
        if risk_metrics and 'prediction_intervals' in risk_metrics:
            intervals = risk_metrics['prediction_intervals']
            lower_95 = intervals['lower_95'][0]
            upper_95 = intervals['upper_95'][0]
            uncertainty = intervals['uncertainty_score'][0]
        else:
            # 默认10%波动区间
            lower_95 = adjusted_price * 0.90
            upper_95 = adjusted_price * 1.10
            uncertainty = 0.10
        
        # 综合变化率
        total_change = (adjusted_price - current_price) / current_price
        
        return {
            'current_price': float(current_price),
            'base_forecast': float(base_forecast),
            'macro_adjusted_forecast': float(adjusted_price),
            'final_forecast_range': {
                'point_estimate': float(adjusted_price),
                'lower_95': float(lower_95),
                'upper_95': float(upper_95)
            },
            'predicted_change': {
                'total_pct': float(total_change * 100),
                'macro_adjustment_pct': float(adjustment_pct * 100)
            },
            'macro_signal': macro_signal,
            'macro_score': float(macro_score),
            'uncertainty': float(uncertainty),
            'confidence_level': '95%'
        }
    
    def _print_summary(self, result: Dict):
        """打印预测摘要"""
        final = result['final_prediction']
        
        print("\n" + "=" * 70)
        print("📋 预测结果摘要")
        print("=" * 70)
        print(f"当前铜价: {final['current_price']:,.2f} 元/吨")
        print(f"基础预测: {final['base_forecast']:,.2f} 元/吨")
        print(f"宏观调整后: {final['macro_adjusted_forecast']:,.2f} 元/吨")
        print(f"最终预测区间 (95%): [{final['final_forecast_range']['lower_95']:,.2f}, {final['final_forecast_range']['upper_95']:,.2f}]")
        print(f"预测变化: {final['predicted_change']['total_pct']:+.2f}%")
        print(f"宏观调整幅度: {final['predicted_change']['macro_adjustment_pct']:+.2f}%")
        print(f"宏观信号: {final['macro_signal']}")
        print(f"不确定性: {final['uncertainty']:.2%}")
        print("=" * 70)


def quick_predict(macro_data: Optional[Dict] = None) -> Dict:
    """
    快速预测函数
    
    Args:
        macro_data: 宏观经济数据字典
        
    Returns:
        预测结果字典
    """
    predictor = EnhancedCopperPredictor()
    return predictor.predict(macro_data=macro_data)


if __name__ == "__main__":
    # 运行增强预测
    result = quick_predict()
    
    # 保存结果到文件
    import json
    
    # 转换 numpy 类型为 Python 原生类型
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj
    
    result_serializable = convert_to_serializable(result)
    
    output_file = f"/Users/ydy/CodeBuddy/20260310193311/output/copper_enhanced_prediction_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_serializable, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 预测结果已保存: {output_file}")
