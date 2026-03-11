"""
改进版 GPR 和 EPU 数据获取模块
使用官方数据源替代代理指标
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import io
import os
import warnings
warnings.filterwarnings('ignore')

class EnhancedDataCollector:
    """增强版 GPR/EPU 数据收集器"""
    
    def __init__(self, cache_dir='./data_cache'):
        self.cache_dir = cache_dir
        self.gpr_url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"
        self.epu_us_url = "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx"
        self.epu_china_url = "https://www.policyuncertainty.com/media/China_Mainland_Paper_EPU.xlsx"
        
        # 创建缓存目录
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, filename):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, filename)
    
    def _is_cache_valid(self, filepath, max_hours=24):
        """检查缓存是否有效（默认24小时）"""
        if not os.path.exists(filepath):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        return (datetime.now() - file_time) < timedelta(hours=max_hours)
    
    def get_gpr_data(self, use_cache=True):
        """
        获取地缘政治风险(GPR)数据
        数据源: https://www.matteoiacoviello.com/gpr.htm
        
        Returns:
            dict: 包含最新GPR值、变化、趋势等
        """
        cache_file = self._get_cache_path('gpr_daily.xls')
        
        try:
            # 检查缓存
            if use_cache and self._is_cache_valid(cache_file):
                print("📁 使用缓存的GPR数据")
                df = pd.read_excel(cache_file)
            else:
                print("🌐 正在下载GPR数据...")
                print(f"   来源: {self.gpr_url}")
                
                # 下载数据
                response = requests.get(self.gpr_url, timeout=30)
                response.raise_for_status()
                
                # 保存缓存
                with open(cache_file, 'wb') as f:
                    f.write(response.content)
                
                # 读取数据
                df = pd.read_excel(io.BytesIO(response.content))
            
            # 解析数据
            # GPR日度数据包含: day, month, year, GPRD (日度指数)
            df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
            df = df.sort_values('date')
            
            # 获取最新值
            latest = df.iloc[-1]
            current_gpr = latest['GPRD']
            current_date = latest['date']
            
            # 计算7天和30天平均值
            gpr_7d = df.tail(7)['GPRD'].mean()
            gpr_30d = df.tail(30)['GPRD'].mean()
            
            # 获取30天前的值计算变化
            gpr_30d_ago = df.iloc[-30]['GPRD'] if len(df) >= 30 else df.iloc[0]['GPRD']
            change_1m = current_gpr - gpr_30d_ago
            
            # 确定趋势
            if current_gpr > gpr_7d * 1.1:
                trend = 'up'
            elif current_gpr < gpr_7d * 0.9:
                trend = 'down'
            else:
                trend = 'stable'
            
            # 计算历史百分位数
            historical_mean = df['GPRD'].mean()
            historical_std = df['GPRD'].std()
            percentile = (df['GPRD'] < current_gpr).mean() * 100
            
            return {
                'value': round(current_gpr, 2),
                'date': current_date.strftime('%Y-%m-%d'),
                'change_1m': round(change_1m, 2),
                'gpr_7d_avg': round(gpr_7d, 2),
                'gpr_30d_avg': round(gpr_30d, 2),
                'trend': trend,
                'historical_mean': round(historical_mean, 2),
                'historical_std': round(historical_std, 2),
                'percentile': round(percentile, 1),
                'data_source': 'Caldara-Iacoviello GPR Index (Official)',
                'reliability': '极高',
                'url': 'https://www.matteoiacoviello.com/gpr.htm',
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ GPR数据获取失败: {e}")
            return {
                'value': None,
                'error': str(e),
                'data_source': 'Caldara-Iacoviello GPR Index',
                'reliability': '失败',
                'status': 'error'
            }
    
    def get_epu_data(self, country='US', use_cache=True):
        """
        获取经济政策不确定性(EPU)数据
        数据源: https://www.policyuncertainty.com/
        
        Args:
            country: 'US' 或 'China'
        
        Returns:
            dict: 包含最新EPU值、变化、趋势等
        """
        if country.upper() == 'US':
            url = self.epu_us_url
            cache_file = self._get_cache_path('epu_us.xlsx')
            source_name = 'US Economic Policy Uncertainty Index'
        else:
            url = self.epu_china_url
            cache_file = self._get_cache_path('epu_china.xlsx')
            source_name = 'China Economic Policy Uncertainty Index'
        
        try:
            # 检查缓存
            if use_cache and self._is_cache_valid(cache_file):
                print(f"📁 使用缓存的EPU-{country}数据")
                df = pd.read_excel(cache_file)
            else:
                print(f"🌐 正在下载EPU-{country}数据...")
                print(f"   来源: {url}")
                
                # 下载数据
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # 保存缓存
                with open(cache_file, 'wb') as f:
                    f.write(response.content)
                
                # 读取数据
                df = pd.read_excel(io.BytesIO(response.content))
            
            # 解析数据
            if country.upper() == 'US':
                # 美国EPU数据格式: Year, Month, EPU
                df['date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
                epu_col = 'EPU'
            else:
                # 中国EPU数据格式: Year, Month, EPU_Mainland_Paper
                df['date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
                epu_col = 'EPU_Mainland_Paper' if 'EPU_Mainland_Paper' in df.columns else 'EPU'
            
            df = df.sort_values('date')
            
            # 获取最新值
            latest = df.iloc[-1]
            current_epu = latest[epu_col]
            current_date = latest['date']
            
            # 获取前一个月的值计算变化
            prev_epu = df.iloc[-2][epu_col] if len(df) >= 2 else current_epu
            change_1m = current_epu - prev_epu
            
            # 计算6个月和12个月平均值
            epu_6m = df.tail(6)[epu_col].mean() if len(df) >= 6 else current_epu
            epu_12m = df.tail(12)[epu_col].mean() if len(df) >= 12 else current_epu
            
            # 确定趋势
            if current_epu > epu_6m * 1.1:
                trend = 'up'
            elif current_epu < epu_6m * 0.9:
                trend = 'down'
            else:
                trend = 'stable'
            
            # 计算历史统计
            historical_mean = df[epu_col].mean()
            historical_std = df[epu_col].std()
            percentile = (df[epu_col] < current_epu).mean() * 100
            
            return {
                'value': round(current_epu, 2),
                'date': current_date.strftime('%Y-%m-%d'),
                'change_1m': round(change_1m, 2),
                'epu_6m_avg': round(epu_6m, 2),
                'epu_12m_avg': round(epu_12m, 2),
                'trend': trend,
                'historical_mean': round(historical_mean, 2),
                'historical_std': round(historical_std, 2),
                'percentile': round(percentile, 1),
                'country': country,
                'data_source': f'{source_name} (Official)',
                'reliability': '极高',
                'url': 'https://www.policyuncertainty.com/',
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ EPU-{country}数据获取失败: {e}")
            return {
                'value': None,
                'country': country,
                'error': str(e),
                'data_source': source_name,
                'reliability': '失败',
                'status': 'error'
            }
    
    def get_all_enhanced_data(self):
        """获取所有增强数据"""
        print("=" * 70)
        print("📊 获取增强版宏观因子数据")
        print("=" * 70)
        
        results = {
            'GPR': self.get_gpr_data(),
            'EPU_US': self.get_epu_data('US'),
            'EPU_China': self.get_epu_data('China')
        }
        
        # 打印汇总
        print("\n" + "=" * 70)
        print("📈 数据获取结果汇总")
        print("=" * 70)
        
        for name, data in results.items():
            status_icon = "✅" if data.get('status') == 'success' else "❌"
            value = data.get('value', 'N/A')
            reliability = data.get('reliability', '未知')
            print(f"{status_icon} {name}: {value} (可信度: {reliability})")
        
        print("=" * 70)
        
        return results


# 兼容旧接口的函数
def get_gpr_index():
    """获取GPR指数（兼容接口）"""
    collector = EnhancedDataCollector()
    result = collector.get_gpr_data()
    
    if result['status'] == 'success':
        return {
            'value': result['value'],
            'change_1m': result['change_1m'],
            'trend': result['trend'],
            'weight': 0.10,
            'impact': 'positive',
            'data_source': result['data_source'],
            'reliability': result['reliability'],
            'percentile': result.get('percentile')
        }
    else:
        # 返回错误时使用备用值
        return {
            'value': 100.0,
            'change_1m': 0,
            'trend': 'stable',
            'weight': 0.10,
            'impact': 'positive',
            'data_source': 'GPR Official (Failed)',
            'reliability': '低',
            'error': result.get('error')
        }

def get_epu_index(country='US'):
    """获取EPU指数（兼容接口）"""
    collector = EnhancedDataCollector()
    result = collector.get_epu_data(country)
    
    if result['status'] == 'success':
        return {
            'value': result['value'],
            'change_1m': result['change_1m'],
            'trend': result['trend'],
            'weight': 0.07,
            'impact': 'positive',
            'data_source': result['data_source'],
            'reliability': result['reliability'],
            'country': result.get('country'),
            'percentile': result.get('percentile')
        }
    else:
        # 返回错误时使用备用值
        return {
            'value': 200.0,
            'change_1m': 0,
            'trend': 'stable',
            'weight': 0.07,
            'impact': 'positive',
            'data_source': f'EPU {country} Official (Failed)',
            'reliability': '低',
            'error': result.get('error')
        }


if __name__ == '__main__':
    # 测试数据获取
    collector = EnhancedDataCollector()
    results = collector.get_all_enhanced_data()
    
    print("\n详细数据:")
    print("-" * 70)
    for name, data in results.items():
        print(f"\n{name}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
