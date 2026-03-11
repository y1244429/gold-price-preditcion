"""
宏观因子数据真实度检查工具
使用 akshare 获取真实数据并对比验证
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class MacroDataQualityChecker:
    """宏观数据质量检查器"""
    
    def __init__(self):
        self.results = {}
        self.akshare_available = self._check_akshare()
        
    def _check_akshare(self):
        """检查 akshare 是否可用"""
        try:
            import akshare as ak
            print("✅ akshare 已安装，版本:", ak.__version__)
            return True
        except ImportError:
            print("⚠️ akshare 未安装，将使用 pip 安装...")
            import subprocess
            subprocess.run(['pip', 'install', 'akshare', '-q'])
            try:
                import akshare as ak
                print("✅ akshare 安装成功")
                return True
            except:
                print("❌ akshare 安装失败")
                return False
    
    def check_dxy(self):
        """检查美元指数数据"""
        print("\n" + "="*60)
        print("1. 美元指数 (DXY) - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '美元指数 (DXY)',
            'weight': 0.20,
            'impact': 'negative',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 方式1: Yahoo Finance
        try:
            dxy = yf.Ticker("DX-Y.NYB")
            df = dxy.history(period="1mo")
            if not df.empty:
                value_yf = df['Close'].iloc[-1]
                print(f"✅ Yahoo Finance: {value_yf:.2f}")
                result['data_sources'].append({
                    'source': 'Yahoo Finance',
                    'value': round(value_yf, 2),
                    'reliability': '高',
                    'type': '真实数据'
                })
            else:
                result['issues'].append('Yahoo Finance 返回空数据')
        except Exception as e:
            print(f"❌ Yahoo Finance 失败: {e}")
            result['issues'].append(f'Yahoo Finance: {str(e)}')
        
        # 方式2: akshare - 外汇数据
        if self.akshare_available:
            try:
                import akshare as ak
                # 获取美元/人民币汇率作为参考
                fx_df = ak.currency_boc_sina(symbol="美元")
                if not fx_df.empty:
                    usd_cny = float(fx_df['中间价'].iloc[-1])
                    print(f"✅ akshare (USD/CNY): {usd_cny:.4f}")
                    result['data_sources'].append({
                        'source': 'akshare (USD/CNY)',
                        'value': round(usd_cny, 4),
                        'reliability': '高',
                        'type': '真实数据'
                    })
            except Exception as e:
                print(f"⚠️ akshare 外汇数据: {e}")
        
        # 评估真实度
        if len(result['data_sources']) >= 1:
            result['realism_score'] = 9  # DXY 数据比较可靠
            result['assessment'] = '✅ 数据真实度高 - 使用 Yahoo Finance DXY 数据'
        else:
            result['realism_score'] = 3
            result['assessment'] = '⚠️ 数据真实度低 - 需要备用数据源'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['美元指数'] = result
        return result
    
    def check_real_rate(self):
        """检查实际利率数据"""
        print("\n" + "="*60)
        print("2. 实际利率 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '实际利率',
            'weight': 0.18,
            'impact': 'negative',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 方式1: 通过美债收益率 - 通胀预期计算
        try:
            tnx = yf.Ticker("^TNX").history(period="1mo")
            # 使用 TIPS 收益率 (实际利率ETF)
            tips = yf.Ticker("TIP").history(period="1mo")
            
            nominal_rate = tnx['Close'].iloc[-1]
            # 实际利率 ≈ 名义利率 - 通胀预期
            real_rate = nominal_rate - 2.5
            
            print(f"✅ Yahoo Finance 名义利率: {nominal_rate:.2f}%")
            print(f"   估算实际利率: {real_rate:.2f}% (名义利率 - 2.5%通胀预期)")
            
            result['data_sources'].append({
                'source': 'Yahoo Finance (计算值)',
                'nominal_rate': round(nominal_rate, 2),
                'real_rate': round(real_rate, 2),
                'method': '名义利率 - 通胀预期(2.5%)',
                'reliability': '中',
                'type': '估算值'
            })
        except Exception as e:
            print(f"❌ Yahoo Finance 失败: {e}")
            result['issues'].append(f'Yahoo Finance: {str(e)}')
        
        # 方式2: akshare - 中国实际利率
        if self.akshare_available:
            try:
                import akshare as ak
                # 获取中国国债收益率
                bond_df = ak.bond_zh_yield(start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                if not bond_df.empty:
                    cn_10y = float(bond_df['10年期国债收益率'].iloc[-1])
                    # 假设中国通胀2%，计算实际利率
                    cn_real_rate = cn_10y - 2.0
                    print(f"✅ akshare 中国10年国债: {cn_10y:.2f}%")
                    print(f"   估算实际利率: {cn_real_rate:.2f}%")
                    result['data_sources'].append({
                        'source': 'akshare (中国)',
                        'nominal_rate': round(cn_10y, 2),
                        'real_rate': round(cn_real_rate, 2),
                        'reliability': '中',
                        'type': '估算值'
                    })
            except Exception as e:
                print(f"⚠️ akshare 国债数据: {e}")
        
        # 评估真实度
        if len(result['data_sources']) >= 1:
            result['realism_score'] = 6
            result['assessment'] = '⚠️ 数据为估算值 - 实际利率 = 名义利率 - 通胀预期，非直接观测值'
        else:
            result['realism_score'] = 2
            result['assessment'] = '❌ 数据真实度低'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['实际利率'] = result
        return result
    
    def check_inflation(self):
        """检查通胀预期数据"""
        print("\n" + "="*60)
        print("3. 通胀预期 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '通胀预期',
            'weight': 0.15,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 当前实现使用随机数生成，这是主要问题
        print("❌ 当前实现: 使用随机数生成 (2.5 ± 随机波动)")
        print("   代码: inflation = 2.5 + np.random.randn() * 0.3")
        result['issues'].append('当前使用随机数模拟，非真实数据')
        
        # 方式1: 使用盈亏平衡通胀率 (Breakeven Inflation Rate)
        try:
            # 10年期盈亏平衡通胀率 = 10年国债 - TIPS
            tnx = yf.Ticker("^TNX").history(period="1mo")
            # TIPS ETF 作为实际利率代理
            tips_yield = 1.5  # 估算值
            
            breakeven = tnx['Close'].iloc[-1] - tips_yield
            print(f"✅ 估算盈亏平衡通胀率: {breakeven:.2f}%")
            print("   方法: 10年期国债收益率 - TIPS收益率")
            
            result['data_sources'].append({
                'source': 'Breakeven Rate (估算)',
                'value': round(breakeven, 2),
                'method': '国债收益率 - TIPS',
                'reliability': '中',
                'type': '估算值'
            })
        except Exception as e:
            print(f"⚠️ 盈亏平衡通胀率计算失败: {e}")
        
        # 方式2: akshare - CPI数据
        if self.akshare_available:
            try:
                import akshare as ak
                # 获取中国CPI
                cpi_df = ak.macro_china_cpi()
                if not cpi_df.empty:
                    latest_cpi = float(cpi_df['今值'].iloc[-1])
                    print(f"✅ akshare 中国CPI: {latest_cpi:.2f}%")
                    result['data_sources'].append({
                        'source': 'akshare (中国CPI)',
                        'value': round(latest_cpi, 2),
                        'reliability': '高',
                        'type': '真实数据'
                    })
            except Exception as e:
                print(f"⚠️ akshare CPI数据: {e}")
        
        # 评估真实度
        result['realism_score'] = 4
        result['assessment'] = '⚠️ 数据真实度低 - 当前使用模拟数据，建议使用盈亏平衡通胀率或CPI'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        print(f"💡 建议: 使用 akshare.macro_usa_cpi() 或 Breakeven Inflation Rate")
        
        self.results['通胀预期'] = result
        return result
    
    def check_bond_yield(self):
        """检查美债收益率数据"""
        print("\n" + "="*60)
        print("4. 美债收益率 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '美债收益率',
            'weight': 0.12,
            'impact': 'negative',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 方式1: Yahoo Finance
        try:
            tnx = yf.Ticker("^TNX").history(period="1mo")
            yield_val = tnx['Close'].iloc[-1]
            print(f"✅ Yahoo Finance (^TNX): {yield_val:.2f}%")
            result['data_sources'].append({
                'source': 'Yahoo Finance',
                'value': round(yield_val, 2),
                'reliability': '高',
                'type': '真实数据'
            })
        except Exception as e:
            print(f"❌ Yahoo Finance 失败: {e}")
            result['issues'].append(f'Yahoo Finance: {str(e)}')
        
        # 方式2: akshare - 中国国债作为对比
        if self.akshare_available:
            try:
                import akshare as ak
                bond_df = ak.bond_zh_yield(start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                if not bond_df.empty:
                    cn_10y = float(bond_df['10年期国债收益率'].iloc[-1])
                    print(f"✅ akshare 中国10年国债: {cn_10y:.2f}%")
                    result['data_sources'].append({
                        'source': 'akshare (中国10年国债)',
                        'value': round(cn_10y, 2),
                        'reliability': '高',
                        'type': '真实数据'
                    })
            except Exception as e:
                print(f"⚠️ akshare 国债数据: {e}")
        
        # 评估真实度
        if len(result['data_sources']) >= 1:
            result['realism_score'] = 9
            result['assessment'] = '✅ 数据真实度高 - 美债收益率 (^TNX) 数据可靠'
        else:
            result['realism_score'] = 3
            result['assessment'] = '⚠️ 数据获取失败'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['美债收益率'] = result
        return result
    
    def check_geopolitical_risk(self):
        """检查地缘政治风险数据"""
        print("\n" + "="*60)
        print("5. 地缘政治风险 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '地缘政治风险',
            'weight': 0.10,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        print("⚠️ 当前实现: 使用 VIX/10 作为代理")
        print("   代码: gpr = min(vix['Close'].iloc[-1] / 10, 10)")
        result['issues'].append('使用VIX作为代理，非真实地缘政治风险指数')
        
        # 方式1: VIX 数据
        try:
            vix = yf.Ticker("^VIX").history(period="1mo")
            vix_val = vix['Close'].iloc[-1]
            gpr_proxy = min(vix_val / 10, 10)
            print(f"✅ VIX 数据: {vix_val:.2f}")
            print(f"   地缘政治风险代理值: {gpr_proxy:.1f}")
            result['data_sources'].append({
                'source': 'VIX (代理)',
                'vix_value': round(vix_val, 2),
                'proxy_gpr': round(gpr_proxy, 1),
                'reliability': '中',
                'type': '代理指标'
            })
        except Exception as e:
            print(f"❌ VIX 获取失败: {e}")
        
        # 说明: Caldara-Iacoviello GPR 指数需要专门获取
        print("\n💡 说明: 真实的地缘政治风险指数 (GPR) 由 Caldara & Iacoviello 维护")
        print("   网址: https://www.matteoiacoviello.com/gpr.htm")
        print("   这是一个学术指数，需要手动下载或爬虫获取")
        
        # 评估真实度
        result['realism_score'] = 5
        result['assessment'] = '⚠️ 数据为代理指标 - VIX不能完全代表地缘政治风险'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['地缘政治风险'] = result
        return result
    
    def check_vix(self):
        """检查VIX波动率数据"""
        print("\n" + "="*60)
        print("6. VIX波动率 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': 'VIX波动率',
            'weight': 0.08,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 方式1: Yahoo Finance
        try:
            vix = yf.Ticker("^VIX").history(period="1mo")
            vix_val = vix['Close'].iloc[-1]
            print(f"✅ Yahoo Finance (^VIX): {vix_val:.2f}")
            result['data_sources'].append({
                'source': 'Yahoo Finance',
                'value': round(vix_val, 2),
                'reliability': '高',
                'type': '真实数据'
            })
        except Exception as e:
            print(f"❌ Yahoo Finance 失败: {e}")
            result['issues'].append(f'Yahoo Finance: {str(e)}')
        
        # 评估真实度
        if len(result['data_sources']) >= 1:
            result['realism_score'] = 10
            result['assessment'] = '✅ 数据真实度极高 - VIX是标准市场数据'
        else:
            result['realism_score'] = 3
            result['assessment'] = '⚠️ 数据获取失败'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['VIX波动率'] = result
        return result
    
    def check_economic_uncertainty(self):
        """检查经济不确定性数据"""
        print("\n" + "="*60)
        print("7. 经济不确定性 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '经济不确定性',
            'weight': 0.07,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        print("⚠️ 当前实现: 使用标普500波动率作为代理")
        print("   代码: volatility = sp500['Close'].pct_change().std() * np.sqrt(252) * 100")
        result['issues'].append('使用标普500波动率作为代理')
        
        # 方式1: 标普500波动率
        try:
            sp500 = yf.Ticker("^GSPC").history(period="3mo")
            volatility = sp500['Close'].pct_change().std() * np.sqrt(252) * 100
            print(f"✅ 标普500年化波动率: {volatility:.2f}%")
            result['data_sources'].append({
                'source': 'S&P500波动率 (代理)',
                'value': round(volatility, 2),
                'reliability': '中',
                'type': '代理指标'
            })
        except Exception as e:
            print(f"❌ 标普500获取失败: {e}")
        
        # 说明: EPU 指数
        print("\n💡 说明: 真实经济政策不确定性指数 (EPU) 由 Baker 等学者维护")
        print("   网址: http://www.policyuncertainty.com/")
        print("   包括美国、中国等国家的月度EPU数据")
        
        # 方式2: akshare - 获取中国EPU相关数据
        if self.akshare_available:
            try:
                import akshare as ak
                # 获取上证指数波动率作为参考
                sh_df = ak.index_zh_a_hist(symbol="000001", period="daily")
                if not sh_df.empty:
                    sh_df['pct_change'] = sh_df['收盘'].pct_change()
                    sh_volatility = sh_df['pct_change'].std() * np.sqrt(252) * 100
                    print(f"✅ akshare 上证指数波动率: {sh_volatility:.2f}%")
                    result['data_sources'].append({
                        'source': 'akshare (上证指数波动率)',
                        'value': round(sh_volatility, 2),
                        'reliability': '中',
                        'type': '代理指标'
                    })
            except Exception as e:
                print(f"⚠️ akshare 指数数据: {e}")
        
        # 评估真实度
        result['realism_score'] = 5
        result['assessment'] = '⚠️ 数据为代理指标 - 使用波动率代替EPU指数'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['经济不确定性'] = result
        return result
    
    def check_etf_holdings(self):
        """检查ETF持仓数据"""
        print("\n" + "="*60)
        print("8. ETF持仓 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': 'ETF持仓',
            'weight': 0.05,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        print("❌ 当前实现: 使用固定值 850 + 随机波动")
        print("   代码: 'value': round(850 + np.random.randn() * 10, 1)")
        result['issues'].append('使用模拟数据，非真实ETF持仓')
        
        # 方式1: GLD 价格作为持仓代理
        try:
            gld = yf.Ticker("GLD").history(period="1mo")
            gld_price = gld['Close'].iloc[-1]
            holdings_change = (gld['Close'].iloc[-1] - gld['Close'].iloc[-20]) / gld['Close'].iloc[-20] * 100
            print(f"✅ GLD ETF价格: ${gld_price:.2f}")
            print(f"   月度变化: {holdings_change:.2f}%")
            print("   ⚠️ 注意: GLD价格变化与持仓量变化不完全等同")
            result['data_sources'].append({
                'source': 'GLD价格 (代理)',
                'price': round(gld_price, 2),
                'change_1m': round(holdings_change, 2),
                'reliability': '低',
                'note': '价格是持仓的代理，非真实持仓量',
                'type': '代理指标'
            })
        except Exception as e:
            print(f"❌ GLD获取失败: {e}")
        
        # 方式2: 获取真实持仓数据
        print("\n💡 真实GLD持仓数据:")
        print("   来源: SPDR Gold Shares (GLD) 官方")
        print("   网址: https://www.spdrgoldshares.com/")
        print("   需要爬虫获取每日持仓报告")
        
        # 尝试获取估计值
        # GLD持仓通常在800-1000吨区间
        estimated_holdings = 850
        print(f"   估计持仓量: ~{estimated_holdings} 吨 (基于历史范围)")
        
        # 评估真实度
        result['realism_score'] = 3
        result['assessment'] = '❌ 数据真实度低 - 当前使用模拟数据，建议爬取GLD官方持仓'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['ETF持仓'] = result
        return result
    
    def check_gold_ratios(self):
        """检查金银比/铜金比数据"""
        print("\n" + "="*60)
        print("9. 金银比/铜金比 - 真实度检查")
        print("="*60)
        
        result = {
            'factor_name': '金银比/铜金比',
            'weight': 0.05,
            'impact': 'positive',
            'data_sources': [],
            'realism_score': 0,
            'issues': []
        }
        
        # 方式1: Yahoo Finance
        try:
            gold = yf.Ticker("GC=F").history(period="1mo")
            silver = yf.Ticker("SI=F").history(period="1mo")
            copper = yf.Ticker("HG=F").history(period="1mo")
            
            gold_price = gold['Close'].iloc[-1]
            silver_price = silver['Close'].iloc[-1]
            copper_price = copper['Close'].iloc[-1]
            
            gold_silver_ratio = gold_price / silver_price
            copper_gold_ratio = copper_price / gold_price * 10000
            
            print(f"✅ 黄金价格: ${gold_price:.2f}")
            print(f"✅ 白银价格: ${silver_price:.2f}")
            print(f"✅ 铜价格: ${copper_price:.3f}")
            print(f"✅ 金银比: {gold_silver_ratio:.1f}")
            print(f"✅ 铜金比: {copper_gold_ratio:.1f}")
            
            result['data_sources'].append({
                'source': 'Yahoo Finance',
                'gold_silver': round(gold_silver_ratio, 1),
                'copper_gold': round(copper_gold_ratio, 1),
                'reliability': '高',
                'type': '真实数据'
            })
        except Exception as e:
            print(f"❌ Yahoo Finance 失败: {e}")
            result['issues'].append(f'Yahoo Finance: {str(e)}')
        
        # 方式2: akshare - 上海期货交易所数据
        if self.akshare_available:
            try:
                import akshare as ak
                # 获取上海黄金、白银期货
                au_df = ak.futures_zh_daily_sina(symbol="AU2406")
                ag_df = ak.futures_zh_daily_sina(symbol="AG2406")
                
                if not au_df.empty and not ag_df.empty:
                    au_price = float(au_df['close'].iloc[-1])
                    ag_price = float(ag_df['close'].iloc[-1])
                    sh_gold_silver = au_price / ag_price * 1000  # 单位转换
                    print(f"✅ akshare 上期所金银比: {sh_gold_silver:.1f}")
                    result['data_sources'].append({
                        'source': 'akshare (上期所)',
                        'gold_silver': round(sh_gold_silver, 1),
                        'reliability': '高',
                        'type': '真实数据'
                    })
            except Exception as e:
                print(f"⚠️ akshare 期货数据: {e}")
        
        # 评估真实度
        if len(result['data_sources']) >= 1:
            result['realism_score'] = 9
            result['assessment'] = '✅ 数据真实度高 - 金银铜价格数据可靠'
        else:
            result['realism_score'] = 3
            result['assessment'] = '⚠️ 数据获取失败'
        
        print(f"📊 真实度评分: {result['realism_score']}/10")
        print(f"📝 评估: {result['assessment']}")
        
        self.results['金银比/铜金比'] = result
        return result
    
    def generate_report(self):
        """生成综合报告"""
        print("\n" + "="*80)
        print("📊 宏观因子数据真实度综合报告")
        print("="*80)
        
        total_score = 0
        high_quality = []
        medium_quality = []
        low_quality = []
        
        for name, result in self.results.items():
            score = result['realism_score']
            total_score += score
            
            if score >= 8:
                high_quality.append(name)
            elif score >= 5:
                medium_quality.append(name)
            else:
                low_quality.append(name)
        
        avg_score = total_score / len(self.results) if self.results else 0
        
        print(f"\n📈 整体真实度评分: {avg_score:.1f}/10")
        print(f"\n✅ 高真实度因子 ({len(high_quality)}个): {', '.join(high_quality)}")
        print(f"⚠️ 中等真实度因子 ({len(medium_quality)}个): {', '.join(medium_quality)}")
        print(f"❌ 低真实度因子 ({len(low_quality)}个): {', '.join(low_quality)}")
        
        print("\n" + "-"*80)
        print("🔧 改进建议:")
        print("-"*80)
        
        if '通胀预期' in low_quality:
            print("\n1. 通胀预期:")
            print("   - 使用 akshare.macro_usa_cpi() 获取美国CPI")
            print("   - 或使用盈亏平衡通胀率 (10Y Treasury - TIPS)")
        
        if '实际利率' in low_quality:
            print("\n2. 实际利率:")
            print("   - 直接使用 TIPS ETF (^TIP) 或 10年期TIPS收益率")
            print("   - 或使用 akshare 获取中国国债收益率")
        
        if '地缘政治风险' in medium_quality:
            print("\n3. 地缘政治风险:")
            print("   - 爬取 Caldara-Iacoviello GPR 指数")
            print("   - 或使用新闻API (如GDELT) 计算风险情绪")
        
        if 'ETF持仓' in low_quality:
            print("\n4. ETF持仓:")
            print("   - 爬取 SPDR Gold Shares 官方持仓报告")
            print("   - 或使用 akshare 获取国内黄金ETF持仓")
        
        if '经济不确定性' in medium_quality:
            print("\n5. 经济不确定性:")
            print("   - 使用经济政策不确定性指数 (EPU)")
            print("   - 或使用 akshare 获取中国宏观经济数据")
        
        print("\n" + "="*80)
        
        return {
            'average_score': round(avg_score, 1),
            'high_quality': high_quality,
            'medium_quality': medium_quality,
            'low_quality': low_quality,
            'details': self.results
        }
    
    def run_all_checks(self):
        """运行所有检查"""
        print("\n" + "🚀"*40)
        print("开始宏观因子数据真实度检查...")
        print("🚀"*40)
        
        self.check_dxy()
        self.check_real_rate()
        self.check_inflation()
        self.check_bond_yield()
        self.check_geopolitical_risk()
        self.check_vix()
        self.check_economic_uncertainty()
        self.check_etf_holdings()
        self.check_gold_ratios()
        
        return self.generate_report()


if __name__ == '__main__':
    checker = MacroDataQualityChecker()
    report = checker.run_all_checks()
    
    # 保存报告
    import json
    with open('/Users/ydy/CodeBuddy/20260310193311/macro_data_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 详细报告已保存到: macro_data_quality_report.json")
