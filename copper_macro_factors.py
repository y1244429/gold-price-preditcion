"""
铜价宏观调整因子系统 - 四层架构设计
基于宏观经济学原理的铜价预测调整模块

架构：
- 第一层：中国实体经济（40%）
- 第二层：美元与流动性（30%）
- 第三层：全球工业周期（20%）
- 第四层：供应与政策冲击（10%）
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import warnings
warnings.filterwarnings('ignore')

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass


class FactorDirection(Enum):
    """因子方向"""
    BULLISH = 1      # 看涨
    BEARISH = -1     # 看跌
    NEUTRAL = 0      # 中性


@dataclass
class FactorResult:
    """单个因子计算结果"""
    name: str
    value: float
    weight: float
    direction: FactorDirection
    score: float      # -1 到 1
    leading_months: int
    confidence: float # 0 到 1
    description: str
    data_source: str = "模拟数据"  # 数据来源: Web Search / API / 模拟数据


@dataclass
class LayerResult:
    """层级计算结果"""
    name: str
    weight: float
    factors: List[FactorResult]
    composite_score: float
    confidence: float


class ChinaRealEconomyFactor:
    """
    第一层：中国实体经济因子（权重40%）
    
    子因子：
    - 房地产周期（15%）：新开工面积、竣工面积、施工面积
    - 基建投资（10%）：电网投资、交运仓储投资
    - 制造业PMI（8%）：官方PMI、财新PMI
    - 信贷脉冲（7%）：社融增速、M1-M2剪刀差
    """
    
    def __init__(self):
        self.layer_weight = 0.40
        self.sub_factors = {
            'real_estate': {'weight': 0.15, 'name': '房地产周期', 'leading': 4},
            'infrastructure': {'weight': 0.10, 'name': '基建投资', 'leading': 0},
            'pmi': {'weight': 0.08, 'name': '制造业PMI', 'leading': 0},
            'credit': {'weight': 0.07, 'name': '信贷脉冲', 'leading': 2}
        }
    
    def calculate(self, data: Dict) -> LayerResult:
        """计算中国实体经济层"""
        factors = []
        
        # 1. 房地产周期因子
        real_estate_factor = self._calc_real_estate_factor(data)
        factors.append(real_estate_factor)
        
        # 2. 基建投资因子
        infra_factor = self._calc_infrastructure_factor(data)
        factors.append(infra_factor)
        
        # 3. 制造业PMI因子
        pmi_factor = self._calc_pmi_factor(data)
        factors.append(pmi_factor)
        
        # 4. 信贷脉冲因子
        credit_factor = self._calc_credit_factor(data)
        factors.append(credit_factor)
        
        # 计算综合得分
        composite_score = sum(f.score * f.weight / self.layer_weight for f in factors)
        confidence = np.mean([f.confidence for f in factors])
        
        return LayerResult(
            name="中国实体经济",
            weight=self.layer_weight,
            factors=factors,
            composite_score=composite_score,
            confidence=confidence
        )
    
    def _calc_real_estate_factor(self, data: Dict) -> FactorResult:
        """房地产周期因子 - 领先3-6个月"""
        try:
            # 获取房地产数据
            starts = data.get('china_housing_starts', 0)
            completed = data.get('china_housing_completed', 0)
            under_construction = data.get('china_housing_under_construction', 0)
            
            # 计算同比变化（使用模拟或实际数据）
            starts_yoy = data.get('housing_starts_yoy', -15)  # 默认-15%
            completed_yoy = data.get('housing_completed_yoy', -10)
            construction_yoy = data.get('construction_yoy', -8)
            
            # 综合得分（-1到1）
            avg_yoy = (starts_yoy + completed_yoy + construction_yoy) / 3
            score = np.clip(avg_yoy / 20, -1, 1)  # 归一化到-1,1
            
            # 确定方向
            if score > 0.2:
                direction = FactorDirection.BULLISH
            elif score < -0.2:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            # 判断数据来源
            data_source = "Web Search" if starts_yoy != -15 else "模拟数据"
            
            return FactorResult(
                name="房地产周期",
                value=avg_yoy,
                weight=self.sub_factors['real_estate']['weight'],
                direction=direction,
                score=score,
                leading_months=4,
                confidence=0.75,
                description=f"新开工{starts_yoy:+.1f}%, 竣工{completed_yoy:+.1f}% (领先3-6个月, 地产用铜占中国需求25-30%)",
                data_source=data_source
            )
        except Exception as e:
            return self._fallback_factor('real_estate', f"计算错误: {e}")
    
    def _calc_infrastructure_factor(self, data: Dict) -> FactorResult:
        """基建投资因子 - 同步至领先1个月"""
        try:
            grid_investment = data.get('grid_investment_yoy', 5)
            transport_investment = data.get('transport_investment_yoy', 3)
            
            avg_growth = (grid_investment + transport_investment) / 2
            score = np.clip(avg_growth / 15, -1, 1)
            
            if score > 0.2:
                direction = FactorDirection.BULLISH
            elif score < -0.2:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="基建投资",
                value=avg_growth,
                weight=self.sub_factors['infrastructure']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.80,
                description=f"电网投资{grid_investment:+.1f}%, 交运{transport_investment:+.1f}% (电网用铜占中国需求15-18%)"
            )
        except Exception as e:
            return self._fallback_factor('infrastructure', f"计算错误: {e}")
    
    def _calc_pmi_factor(self, data: Dict) -> FactorResult:
        """制造业PMI因子 - 同步指标"""
        try:
            official_pmi = data.get('official_pmi', 50)
            caixin_pmi = data.get('caixin_pmi', 50)
            
            # PMI > 50 扩张，< 50 收缩
            avg_pmi = (official_pmi + caixin_pmi) / 2
            score = np.clip((avg_pmi - 50) / 5, -1, 1)
            
            if avg_pmi > 51:
                direction = FactorDirection.BULLISH
            elif avg_pmi < 49:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            # 判断数据来源
            data_source = "Web Search" if official_pmi != 50 else "模拟数据"
            
            return FactorResult(
                name="制造业PMI",
                value=avg_pmi,
                weight=self.sub_factors['pmi']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.85,
                description=f"官方PMI:{official_pmi:.1f}, 财新PMI:{caixin_pmi:.1f} (工业产出前瞻指标)",
                data_source=data_source
            )
        except Exception as e:
            return self._fallback_factor('pmi', f"计算错误: {e}")
    
    def _calc_credit_factor(self, data: Dict) -> FactorResult:
        """信贷脉冲因子 - 领先2-3个月"""
        try:
            social_finance = data.get('social_finance_yoy', 8)
            m1_m2_scissors = data.get('m1_m2_scissors', -2)
            
            # 信贷脉冲 = 社融增速 + M1-M2剪刀差影响
            credit_impulse = social_finance + m1_m2_scissors * 2
            score = np.clip(credit_impulse / 20, -1, 1)
            
            if score > 0.2:
                direction = FactorDirection.BULLISH
            elif score < -0.2:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="信贷脉冲",
                value=credit_impulse,
                weight=self.sub_factors['credit']['weight'],
                direction=direction,
                score=score,
                leading_months=2,
                confidence=0.70,
                description=f"社融增速{social_finance:+.1f}%, M1-M2剪刀差{m1_m2_scissors:+.1f}% (领先2-3个月, 流动性→投资→铜需求)"
            )
        except Exception as e:
            return self._fallback_factor('credit', f"计算错误: {e}")
    
    def _fallback_factor(self, key: str, error_msg: str) -> FactorResult:
        """返回默认因子"""
        config = self.sub_factors[key]
        return FactorResult(
            name=config['name'],
            value=0,
            weight=config['weight'],
            direction=FactorDirection.NEUTRAL,
            score=0,
            leading_months=config['leading'],
            confidence=0.5,
            description=f"数据不可用 - {error_msg}",
            data_source="模拟数据"
        )


class DollarLiquidityFactor:
    """
    第二层：美元与流动性因子（权重30%）
    
    子因子：
    - 美元指数DXY（15%）：美元对一篮子货币汇率
    - 实际利率（8%）：10Y TIPS收益率
    - 美联储政策（4%）：联邦基金利率、缩表进度
    - 离岸美元流动性（3%）：SOFR-OIS利差、FRA-OIS
    """
    
    def __init__(self):
        self.layer_weight = 0.30
        self.sub_factors = {
            'dxy': {'weight': 0.15, 'name': '美元指数', 'correlation': -0.80},
            'real_rate': {'weight': 0.08, 'name': '实际利率', 'correlation': -0.65},
            'fed_policy': {'weight': 0.04, 'name': '美联储政策'},
            'offshore_liquidity': {'weight': 0.03, 'name': '离岸美元流动性'}
        }
    
    def calculate(self, data: Dict) -> LayerResult:
        """计算美元与流动性层"""
        factors = []
        
        # 1. 美元指数因子
        dxy_factor = self._calc_dxy_factor(data)
        factors.append(dxy_factor)
        
        # 2. 实际利率因子
        real_rate_factor = self._calc_real_rate_factor(data)
        factors.append(real_rate_factor)
        
        # 3. 美联储政策因子
        fed_factor = self._calc_fed_factor(data)
        factors.append(fed_factor)
        
        # 4. 离岸美元流动性因子
        liquidity_factor = self._calc_liquidity_factor(data)
        factors.append(liquidity_factor)
        
        composite_score = sum(f.score * f.weight / self.layer_weight for f in factors)
        confidence = np.mean([f.confidence for f in factors])
        
        return LayerResult(
            name="美元与流动性",
            weight=self.layer_weight,
            factors=factors,
            composite_score=composite_score,
            confidence=confidence
        )
    
    def _calc_dxy_factor(self, data: Dict) -> FactorResult:
        """美元指数因子 - 负相关-0.75至-0.85"""
        try:
            dxy = data.get('dxy_index', 103)
            dxy_change = data.get('dxy_change_3m', 0)
            
            # 美元强势 = 铜价压力（负相关）
            # 使用3个月变化率
            score = -np.clip(dxy_change / 5, -1, 1)  # 负相关
            
            if dxy_change < -2:
                direction = FactorDirection.BULLISH
            elif dxy_change > 2:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            # 判断数据来源: Web Search > API > 默认
            if dxy != 103:
                data_source = "Web Search"  # Web Search获取的数据不等于默认值
            elif dxy_change != 0:
                data_source = "yfinance API"
            else:
                data_source = "模拟数据"
            
            return FactorResult(
                name="美元指数",
                value=dxy,
                weight=self.sub_factors['dxy']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.85,
                description=f"DXY:{dxy:.2f}, 3月变化{dxy_change:+.1f}% (负相关-0.80, 定价货币效应)",
                data_source=data_source
            )
        except Exception as e:
            return self._fallback_factor('dxy', str(e))
    
    def _calc_real_rate_factor(self, data: Dict) -> FactorResult:
        """实际利率因子 - 负相关-0.60至-0.70"""
        try:
            tips_yield = data.get('tips_10y', 1.5)
            tips_change = data.get('tips_change_3m', 0)
            
            # 实际利率上升 = 持有成本增加 = 铜价压力
            score = -np.clip((tips_yield - 1.0) / 2, -1, 1)
            
            if tips_yield < 1.0:
                direction = FactorDirection.BULLISH
            elif tips_yield > 2.0:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="实际利率",
                value=tips_yield,
                weight=self.sub_factors['real_rate']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.80,
                description=f"10Y TIPS:{tips_yield:.2f}% (负相关-0.65, 持有成本+机会成本)"
            )
        except Exception as e:
            return self._fallback_factor('real_rate', str(e))
    
    def _calc_fed_factor(self, data: Dict) -> FactorResult:
        """美联储政策因子"""
        try:
            fed_rate = data.get('fed_funds_rate', 5.25)
            qt_progress = data.get('qt_progress', 50)  # 缩表进度百分比
            
            # 综合政策紧缩程度
            tightening_score = (fed_rate / 6) * 0.6 + (qt_progress / 100) * 0.4
            score = -np.clip(tightening_score, -1, 1)
            
            if fed_rate < 4.0:
                direction = FactorDirection.BULLISH
            elif fed_rate > 5.0 and qt_progress > 50:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            # 判断数据来源
            data_source = "Web Search" if fed_rate != 5.25 else "模拟数据"
            
            return FactorResult(
                name="美联储政策",
                value=fed_rate,
                weight=self.sub_factors['fed_policy']['weight'],
                direction=direction,
                score=score,
                leading_months=3,
                confidence=0.75,
                description=f"联邦基金利率:{fed_rate:.2f}%, 缩表进度{qt_progress:.0f}% (中期主导, 全球流动性总闸门)",
                data_source=data_source
            )
        except Exception as e:
            return self._fallback_factor('fed_policy', str(e))
    
    def _calc_liquidity_factor(self, data: Dict) -> FactorResult:
        """离岸美元流动性因子 - 危机时飙升"""
        try:
            sofr_ois = data.get('sofr_ois_spread', 10)  # 基点
            fra_ois = data.get('fra_ois_spread', 15)
            
            avg_spread = (sofr_ois + fra_ois) / 2
            # 利差扩大 = 美元融资紧张 = 铜价压力
            score = -np.clip((avg_spread - 20) / 40, -1, 1)
            
            if avg_spread > 50:
                direction = FactorDirection.BEARISH
            elif avg_spread < 15:
                direction = FactorDirection.BULLISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="离岸美元流动性",
                value=avg_spread,
                weight=self.sub_factors['offshore_liquidity']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.70,
                description=f"SOFR-OIS:{sofr_ois:.0f}bp, FRA-OIS:{fra_ois:.0f}bp (危机时飙升, 美元融资紧张度)"
            )
        except Exception as e:
            return self._fallback_factor('offshore_liquidity', str(e))
    
    def _fallback_factor(self, key: str, error_msg: str) -> FactorResult:
        config = self.sub_factors[key]
        return FactorResult(
            name=config['name'],
            value=0,
            weight=config['weight'],
            direction=FactorDirection.NEUTRAL,
            score=0,
            leading_months=0,
            confidence=0.5,
            description=f"数据不可用 - {error_msg}",
            data_source="模拟数据"
        )


class GlobalIndustrialCycleFactor:
    """
    第三层：全球工业周期因子（权重20%）
    
    子因子：
    - 全球制造业PMI（8%）：JPMorgan全球制造业PMI
    - 美国ISM制造业（5%）：ISM Manufacturing
    - 欧元区工业产出（4%）：Eurostat工业生产指数
    - 库存周期（3%）：美国制造商库存销售比
    """
    
    def __init__(self):
        self.layer_weight = 0.20
        self.sub_factors = {
            'global_pmi': {'weight': 0.08, 'name': '全球制造业PMI'},
            'us_ism': {'weight': 0.05, 'name': '美国ISM制造业'},
            'eu_industry': {'weight': 0.04, 'name': '欧元区工业产出'},
            'inventory': {'weight': 0.03, 'name': '库存周期'}
        }
    
    def calculate(self, data: Dict) -> LayerResult:
        """计算全球工业周期层"""
        factors = []
        
        # 1. 全球制造业PMI
        global_pmi_factor = self._calc_global_pmi_factor(data)
        factors.append(global_pmi_factor)
        
        # 2. 美国ISM制造业
        us_ism_factor = self._calc_us_ism_factor(data)
        factors.append(us_ism_factor)
        
        # 3. 欧元区工业产出
        eu_factor = self._calc_eu_factor(data)
        factors.append(eu_factor)
        
        # 4. 库存周期
        inventory_factor = self._calc_inventory_factor(data)
        factors.append(inventory_factor)
        
        composite_score = sum(f.score * f.weight / self.layer_weight for f in factors)
        confidence = np.mean([f.confidence for f in factors])
        
        return LayerResult(
            name="全球工业周期",
            weight=self.layer_weight,
            factors=factors,
            composite_score=composite_score,
            confidence=confidence
        )
    
    def _calc_global_pmi_factor(self, data: Dict) -> FactorResult:
        """全球制造业PMI因子"""
        try:
            global_pmi = data.get('global_manufacturing_pmi', 50)
            score = np.clip((global_pmi - 50) / 3, -1, 1)
            
            if global_pmi > 51.5:
                direction = FactorDirection.BULLISH
            elif global_pmi < 48.5:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="全球制造业PMI",
                value=global_pmi,
                weight=self.sub_factors['global_pmi']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.85,
                description=f"JPM全球制造业PMI:{global_pmi:.1f} (全球, 有效性:高)"
            )
        except Exception as e:
            return self._fallback_factor('global_pmi', str(e))
    
    def _calc_us_ism_factor(self, data: Dict) -> FactorResult:
        """美国ISM制造业因子"""
        try:
            ism = data.get('us_ism_manufacturing', 50)
            new_orders = data.get('ism_new_orders', 50)
            
            avg_ism = (ism + new_orders) / 2
            score = np.clip((avg_ism - 50) / 5, -1, 1)
            
            if avg_ism > 52:
                direction = FactorDirection.BULLISH
            elif avg_ism < 48:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="美国ISM制造业",
                value=ism,
                weight=self.sub_factors['us_ism']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.80,
                description=f"ISM:{ism:.1f}, 新订单:{new_orders:.1f} (北美, 有效性:中高)"
            )
        except Exception as e:
            return self._fallback_factor('us_ism', str(e))
    
    def _calc_eu_factor(self, data: Dict) -> FactorResult:
        """欧元区工业产出因子"""
        try:
            eu_industrial = data.get('eu_industrial_production', 0)
            
            score = np.clip(eu_industrial / 5, -1, 1)
            
            if eu_industrial > 2:
                direction = FactorDirection.BULLISH
            elif eu_industrial < -2:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="欧元区工业产出",
                value=eu_industrial,
                weight=self.sub_factors['eu_industry']['weight'],
                direction=direction,
                score=score,
                leading_months=1,
                confidence=0.70,
                description=f"Eurostat工业生产同比:{eu_industrial:+.1f}% (欧洲, 有效性:中等)"
            )
        except Exception as e:
            return self._fallback_factor('eu_industry', str(e))
    
    def _calc_inventory_factor(self, data: Dict) -> FactorResult:
        """库存周期因子 - 滞后确认"""
        try:
            inventory_ratio = data.get('us_inventory_sales_ratio', 1.4)
            
            # 库存销售比低于均值 = 补库需求 = 铜价支撑
            deviation = (1.4 - inventory_ratio) / 0.3
            score = np.clip(deviation, -1, 1)
            
            if inventory_ratio < 1.35:
                direction = FactorDirection.BULLISH
            elif inventory_ratio > 1.45:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="库存周期",
                value=inventory_ratio,
                weight=self.sub_factors['inventory']['weight'],
                direction=direction,
                score=score,
                leading_months=-1,
                confidence=0.65,
                description=f"美国制造商库存销售比:{inventory_ratio:.2f} (滞后确认指标)"
            )
        except Exception as e:
            return self._fallback_factor('inventory', str(e))
    
    def _fallback_factor(self, key: str, error_msg: str) -> FactorResult:
        config = self.sub_factors[key]
        return FactorResult(
            name=config['name'],
            value=0,
            weight=config['weight'],
            direction=FactorDirection.NEUTRAL,
            score=0,
            leading_months=0,
            confidence=0.5,
            description=f"数据不可用 - {error_msg}",
            data_source="模拟数据"
        )


class SupplyPolicyFactor:
    """
    第四层：供应与政策冲击因子（权重10%）
    
    子因子：
    - 铜精矿供应（4%）：智利+秘鲁产量、TC/RC
    - 地缘与政策（3%）：主要产国政策变动、罢工
    - 库存水平（2%）：全球显性库存可用天数
    - 碳政策（1%）：欧盟CBAM、中国能耗双控
    """
    
    def __init__(self):
        self.layer_weight = 0.10
        self.sub_factors = {
            'mine_supply': {'weight': 0.04, 'name': '铜精矿供应'},
            'geopolitics': {'weight': 0.03, 'name': '地缘与政策'},
            'inventory': {'weight': 0.02, 'name': '库存水平'},
            'carbon_policy': {'weight': 0.01, 'name': '碳政策'}
        }
    
    def calculate(self, data: Dict) -> LayerResult:
        """计算供应与政策冲击层"""
        factors = []
        
        # 1. 铜精矿供应
        mine_factor = self._calc_mine_supply_factor(data)
        factors.append(mine_factor)
        
        # 2. 地缘与政策
        geo_factor = self._calc_geopolitics_factor(data)
        factors.append(geo_factor)
        
        # 3. 库存水平
        inventory_factor = self._calc_inventory_factor(data)
        factors.append(inventory_factor)
        
        # 4. 碳政策
        carbon_factor = self._calc_carbon_factor(data)
        factors.append(carbon_factor)
        
        composite_score = sum(f.score * f.weight / self.layer_weight for f in factors)
        confidence = np.mean([f.confidence for f in factors])
        
        return LayerResult(
            name="供应与政策冲击",
            weight=self.layer_weight,
            factors=factors,
            composite_score=composite_score,
            confidence=confidence
        )
    
    def _calc_mine_supply_factor(self, data: Dict) -> FactorResult:
        """铜精矿供应因子 - TC/RC是供应紧张度指标"""
        try:
            tc_rc = data.get('copper_tc_rc', 25)  # 美元/吨
            chile_output = data.get('chile_copper_output', 0)
            peru_output = data.get('peru_copper_output', 0)
            
            # TC/RC越低 = 精矿越紧张 = 铜价支撑
            # 2024年TC跌至负值是极端情况
            if tc_rc < 0:
                score = 0.8  # 极度看涨
            else:
                score = np.clip((50 - tc_rc) / 50, -1, 1)
            
            if tc_rc < 20:
                direction = FactorDirection.BULLISH
            elif tc_rc > 60:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            # 判断数据来源
            data_source = "Web Search" if tc_rc != 25 else "模拟数据"
            
            return FactorResult(
                name="铜精矿供应",
                value=tc_rc,
                weight=self.sub_factors['mine_supply']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.75,
                description=f"TC/RC:{tc_rc:.1f}$/吨 (月度, 冲击强度高, 2024年TC跌至负值)",
                data_source=data_source
            )
        except Exception as e:
            return self._fallback_factor('mine_supply', str(e))
    
    def _calc_geopolitics_factor(self, data: Dict) -> FactorResult:
        """地缘与政策因子 - 事件驱动"""
        try:
            # 风险事件评分
            strike_risk = data.get('strike_risk_score', 3)  # 1-10
            policy_risk = data.get('policy_risk_score', 3)
            
            risk_score = (strike_risk + policy_risk) / 2
            # 风险高 = 供应担忧 = 铜价支撑
            score = np.clip((risk_score - 5) / 5, -1, 1)
            
            if risk_score > 6:
                direction = FactorDirection.BULLISH
            elif risk_score < 3:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="地缘与政策",
                value=risk_score,
                weight=self.sub_factors['geopolitics']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.60,
                description=f"罢工风险:{strike_risk}/10, 政策风险:{policy_risk}/10 (事件驱动, 冲击强度极高)"
            )
        except Exception as e:
            return self._fallback_factor('geopolitics', str(e))
    
    def _calc_inventory_factor(self, data: Dict) -> FactorResult:
        """库存水平因子 - 验证供需"""
        try:
            inventory_days = data.get('global_copper_inventory_days', 5)
            
            # 库存天数低 = 供应紧张
            score = np.clip((5 - inventory_days) / 3, -1, 1)
            
            if inventory_days < 4:
                direction = FactorDirection.BULLISH
            elif inventory_days > 7:
                direction = FactorDirection.BEARISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="库存水平",
                value=inventory_days,
                weight=self.sub_factors['inventory']['weight'],
                direction=direction,
                score=score,
                leading_months=0,
                confidence=0.80,
                description=f"全球显性库存可用天数:{inventory_days:.1f}天 (周度, 验证供需)"
            )
        except Exception as e:
            return self._fallback_factor('inventory', str(e))
    
    def _calc_carbon_factor(self, data: Dict) -> FactorResult:
        """碳政策因子 - 长期结构性影响"""
        try:
            cbam_impact = data.get('eu_cbam_impact', 5)  # 成本增加百分比
            china_energy_control = data.get('china_energy_control', 5)
            
            # 碳政策越严格 = 供应成本上升 = 长期支撑铜价
            avg_impact = (cbam_impact + china_energy_control) / 2
            score = np.clip(avg_impact / 10, -1, 1)
            
            if avg_impact > 7:
                direction = FactorDirection.BULLISH
            else:
                direction = FactorDirection.NEUTRAL
            
            return FactorResult(
                name="碳政策",
                value=avg_impact,
                weight=self.sub_factors['carbon_policy']['weight'],
                direction=direction,
                score=score,
                leading_months=6,
                confidence=0.70,
                description=f"CBAM成本影响:{cbam_impact:.1f}%, 中国能耗双控:{china_energy_control:.1f}% (季度, 长期结构性)"
            )
        except Exception as e:
            return self._fallback_factor('carbon_policy', str(e))
    
    def _fallback_factor(self, key: str, error_msg: str) -> FactorResult:
        config = self.sub_factors[key]
        return FactorResult(
            name=config['name'],
            value=0,
            weight=config['weight'],
            direction=FactorDirection.NEUTRAL,
            score=0,
            leading_months=0,
            confidence=0.5,
            description=f"数据不可用 - {error_msg}",
            data_source="模拟数据"
        )


class CopperMacroAdjustmentSystem:
    """
    铜价宏观调整因子系统 - 主控制器
    
    整合四层因子，生成最终的预测调整信号
    """
    
    def __init__(self):
        self.china_layer = ChinaRealEconomyFactor()
        self.dollar_layer = DollarLiquidityFactor()
        self.industrial_layer = GlobalIndustrialCycleFactor()
        self.supply_layer = SupplyPolicyFactor()
        
        self.history = []
    
    def calculate(self, macro_data: Dict) -> Dict:
        """
        计算所有因子并生成综合调整信号
        
        Args:
            macro_data: 宏观经济数据字典
            
        Returns:
            包含所有层级结果和综合信号的字典
        """
        # 计算各层
        china_result = self.china_layer.calculate(macro_data)
        dollar_result = self.dollar_layer.calculate(macro_data)
        industrial_result = self.industrial_layer.calculate(macro_data)
        supply_result = self.supply_layer.calculate(macro_data)
        
        # 综合得分（加权平均）
        composite_score = (
            china_result.composite_score * china_result.weight +
            dollar_result.composite_score * dollar_result.weight +
            industrial_result.composite_score * industrial_result.weight +
            supply_result.composite_score * supply_result.weight
        )
        
        # 整体置信度
        overall_confidence = np.mean([
            china_result.confidence,
            dollar_result.confidence,
            industrial_result.confidence,
            supply_result.confidence
        ])
        
        # 生成交易信号
        signal = self._generate_signal(composite_score, overall_confidence)
        
        # 调整幅度建议
        adjustment = self._calculate_adjustment(composite_score, overall_confidence)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'composite_score': composite_score,
            'overall_confidence': overall_confidence,
            'signal': signal,
            'adjustment': adjustment,
            'layers': {
                'china_real_economy': {
                    'name': china_result.name,
                    'weight': china_result.weight,
                    'score': china_result.composite_score,
                    'confidence': china_result.confidence,
                    'factors': self._factor_to_dict(china_result.factors)
                },
                'dollar_liquidity': {
                    'name': dollar_result.name,
                    'weight': dollar_result.weight,
                    'score': dollar_result.composite_score,
                    'confidence': dollar_result.confidence,
                    'factors': self._factor_to_dict(dollar_result.factors)
                },
                'global_industrial': {
                    'name': industrial_result.name,
                    'weight': industrial_result.weight,
                    'score': industrial_result.composite_score,
                    'confidence': industrial_result.confidence,
                    'factors': self._factor_to_dict(industrial_result.factors)
                },
                'supply_policy': {
                    'name': supply_result.name,
                    'weight': supply_result.weight,
                    'score': supply_result.composite_score,
                    'confidence': supply_result.confidence,
                    'factors': self._factor_to_dict(supply_result.factors)
                }
            }
        }
        
        self.history.append(result)
        return result
    
    def _factor_to_dict(self, factors: List[FactorResult]) -> List[Dict]:
        """转换因子结果为字典"""
        return [{
            'name': f.name,
            'value': round(f.value, 2),
            'weight': f.weight,
            'direction': f.direction.name,
            'score': round(f.score, 3),
            'leading_months': f.leading_months,
            'confidence': round(f.confidence, 2),
            'description': f.description,
            'data_source': f.data_source
        } for f in factors]
    
    def _generate_signal(self, score: float, confidence: float) -> str:
        """生成交易信号"""
        if confidence < 0.5:
            return "数据不足，无法生成信号"
        
        if score > 0.5:
            return "强烈看多"
        elif score > 0.2:
            return "看多"
        elif score > -0.2:
            return "中性"
        elif score > -0.5:
            return "看空"
        else:
            return "强烈看空"
    
    def _calculate_adjustment(self, score: float, confidence: float) -> Dict:
        """计算预测调整幅度"""
        # 基础调整系数（-20% 到 +20%）
        base_adjustment = score * 0.20
        
        # 根据置信度调整
        effective_adjustment = base_adjustment * confidence
        
        return {
            'price_adjustment_pct': round(effective_adjustment * 100, 2),
            'position_sizing_factor': round(1 + effective_adjustment * 0.5, 2),
            'confidence_adjusted': round(confidence, 2)
        }
    
    def get_summary(self, result: Dict) -> str:
        """生成可读性摘要"""
        lines = []
        lines.append("=" * 70)
        lines.append("🔶 铜价宏观调整因子分析")
        lines.append("=" * 70)
        lines.append(f"综合得分: {result['composite_score']:+.3f}")
        lines.append(f"整体置信度: {result['overall_confidence']:.1%}")
        lines.append(f"交易信号: {result['signal']}")
        lines.append(f"价格调整建议: {result['adjustment']['price_adjustment_pct']:+.1f}%")
        lines.append("")
        
        for layer_key, layer in result['layers'].items():
            lines.append(f"\n【{layer['name']}】权重{layer['weight']:.0%} | 得分{layer['score']:+.3f}")
            lines.append("-" * 70)
            for factor in layer['factors']:
                emoji = "📈" if factor['direction'] == 'BULLISH' else "📉" if factor['direction'] == 'BEARISH' else "➡️"
                lines.append(f"  {emoji} {factor['name']} (权重{factor['weight']:.0%})")
                lines.append(f"     数值: {factor['value']}, 得分: {factor['score']:+.3f}, 置信度: {factor['confidence']:.0%}")
                lines.append(f"     {factor['description']}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


# ============ 便捷函数 ============

def get_default_macro_data() -> Dict:
    """
    获取默认的宏观经济数据
    优先级：
    1. 整合数据（API + Web Search）
    2. API 真实数据
    3. 默认模拟数据
    """
    # 尝试获取整合数据（API + Web Search）
    try:
        from copper_macro_integrated import get_enhanced_macro_data
        print("🔄 尝试获取整合宏观数据（API + Web Search）...")
        data = get_enhanced_macro_data()
        if data and len(data) > 5:
            print("✅ 使用整合宏观数据（API + Web Search）")
            return data
    except Exception as e:
        print(f"⚠️ 获取整合数据失败: {e}")
    
    # 尝试获取 API 真实数据
    try:
        from copper_real_macro_data import CopperRealMacroDataCollector
        collector = CopperRealMacroDataCollector()
        real_data = collector.get_all_real_data()
        if real_data and len(real_data) > 5:
            print("✅ 使用 API 真实宏观数据")
            return real_data
    except Exception as e:
        print(f"⚠️ 获取 API 数据失败: {e}")
    
    # 使用默认模拟数据
    print("⚠️ 使用默认模拟数据")
    return {
        # 中国房地产数据
        'housing_starts_yoy': -18.5,
        'housing_completed_yoy': -12.3,
        'construction_yoy': -9.8,
        
        # 基建投资
        'grid_investment_yoy': 8.5,
        'transport_investment_yoy': 4.2,
        
        # PMI
        'official_pmi': 49.8,
        'caixin_pmi': 51.2,
        
        # 信贷
        'social_finance_yoy': 9.5,
        'm1_m2_scissors': -3.2,
        
        # 美元流动性
        'dxy_index': 103.5,
        'dxy_change_3m': 1.2,
        'tips_10y': 1.8,
        'fed_funds_rate': 5.25,
        'qt_progress': 65,
        'sofr_ois_spread': 12,
        'fra_ois_spread': 18,
        
        # 全球工业
        'global_manufacturing_pmi': 50.3,
        'us_ism_manufacturing': 48.5,
        'ism_new_orders': 49.2,
        'eu_industrial_production': -1.5,
        'us_inventory_sales_ratio': 1.38,
        
        # 供应与政策
        'copper_tc_rc': -5,  # 负值表示极端紧张
        'strike_risk_score': 4,
        'policy_risk_score': 3,
        'global_copper_inventory_days': 4.5,
        'eu_cbam_impact': 3,
        'china_energy_control': 4
    }


def calculate_copper_adjustment(macro_data: Optional[Dict] = None) -> Dict:
    """
    计算铜价宏观调整因子
    
    Args:
        macro_data: 宏观经济数据，如果为None则使用默认数据
        
    Returns:
        调整因子结果字典
    """
    if macro_data is None:
        macro_data = get_default_macro_data()
    
    system = CopperMacroAdjustmentSystem()
    result = system.calculate(macro_data)
    
    return result


if __name__ == "__main__":
    # 测试代码
    print("=" * 70)
    print("🔶 铜价宏观调整因子系统测试")
    print("=" * 70)
    
    # 使用默认数据测试
    result = calculate_copper_adjustment()
    
    # 打印详细摘要
    system = CopperMacroAdjustmentSystem()
    print(system.get_summary(result))
    
    # 输出JSON格式
    print("\n\n📊 JSON输出格式:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
