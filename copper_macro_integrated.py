"""
铜价宏观数据 - 整合所有数据源
优先级：
1. Web Search (Serper/Tavily) - 最新新闻数据
2. API数据源 (akshare/yfinance) - 实时市场数据
3. 默认值 - 备用数据
"""

import os
from typing import Dict
from copper_real_macro_data import CopperRealMacroDataCollector
from copper_macro_web_search import CopperMacroWebSearch

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("✅ 已加载 .env 环境变量")
except ImportError:
    pass  # python-dotenv 未安装时跳过


class CopperMacroIntegratedCollector:
    """整合所有数据源的铜价宏观数据收集器"""
    
    def __init__(self):
        self.api_collector = CopperRealMacroDataCollector()
        self.web_collector = CopperMacroWebSearch()
    
    def get_integrated_data(self, use_web_search: bool = True) -> Dict:
        """
        获取整合的宏观数据
        
        Args:
            use_web_search: 是否使用 Web Search（需要 API Key）
        
        Returns:
            Dict: 整合后的宏观数据
        """
        print("=" * 70)
        print("🔶 铜价宏观数据 - 整合收集器")
        print("=" * 70)
        
        # 1. 首先获取 API 数据（基础数据）
        print("\n📊 步骤1: 获取 API 数据源...")
        api_data = self.api_collector.get_all_real_data()
        
        # 2. 尝试获取 Web Search 数据（补充/验证）
        web_data = {}
        if use_web_search:
            print("\n🌐 步骤2: 获取 Web Search 数据...")
            web_data = self.web_collector.get_all_web_data()
        
        # 3. 整合数据（Web Search 优先，因为更新）
        print("\n🔀 步骤3: 整合数据...")
        integrated_data = api_data.copy()
        
        # 用 Web 数据覆盖 API 数据（Web 数据通常更新）
        for key, value in web_data.items():
            if value is not None:
                if key in integrated_data:
                    print(f"  📝 {key}: API={integrated_data[key]} → Web={value}")
                else:
                    print(f"  ➕ {key}: 新增 Web={value}")
                integrated_data[key] = value
        
        # 4. 数据质量评估
        print("\n📈 数据质量评估:")
        web_count = len([k for k in web_data.keys() if web_data[k] is not None])
        api_count = len([k for k in api_data.keys() if api_data[k] is not None])
        total_count = len(integrated_data)
        
        print(f"  • Web Search 数据: {web_count} 个")
        print(f"  • API 数据源: {api_count} 个")
        print(f"  • 整合后总数: {total_count} 个")
        print(f"  • 真实数据占比: {(web_count + api_count) / total_count * 100:.1f}%")
        
        print("\n" + "=" * 70)
        print("✅ 数据整合完成")
        print("=" * 70)
        
        return integrated_data
    
    def print_comparison(self, api_data: Dict, web_data: Dict, integrated_data: Dict):
        """打印数据对比"""
        print("\n📊 数据源对比:")
        print("-" * 70)
        
        key_metrics = [
            'official_pmi', 'caixin_pmi', 'us_ism_manufacturing',
            'dxy_index', 'copper_tc_rc', 'housing_starts_yoy'
        ]
        
        for key in key_metrics:
            api_val = api_data.get(key, 'N/A')
            web_val = web_data.get(key, 'N/A')
            final_val = integrated_data.get(key, 'N/A')
            
            source = "Web" if key in web_data and web_data[key] is not None else \
                     "API" if key in api_data and api_data[key] is not None else "默认"
            
            print(f"  {key:25s} | API: {str(api_val):10s} | Web: {str(web_val):10s} | 最终: {final_val} ({source})")


# 便捷函数
def get_integrated_macro_data(use_web_search: bool = True) -> Dict:
    """
    获取整合宏观数据的便捷函数
    
    Args:
        use_web_search: 是否使用 Web Search（需要 SERPER_API_KEY 或 TAVILY_API_KEY）
    
    Returns:
        Dict: 整合后的宏观数据
    """
    collector = CopperMacroIntegratedCollector()
    data = collector.get_integrated_data(use_web_search=use_web_search)
    return data


# 更新 copper_macro_factors.py 的 get_default_macro_data 函数
def get_enhanced_macro_data() -> Dict:
    """
    获取增强版宏观数据（整合所有数据源）
    供 copper_macro_factors.py 调用
    """
    try:
        collector = CopperMacroIntegratedCollector()
        # 检查是否有 Web Search API Key
        has_web_key = bool(
            os.getenv('SERPER_API_KEY') or 
            os.getenv('TAVILY_API_KEY')
        )
        return collector.get_integrated_data(use_web_search=has_web_key)
    except Exception as e:
        print(f"⚠️ 整合数据获取失败: {e}")
        # 回退到基础 API 数据
        try:
            from copper_real_macro_data import get_real_macro_data
            return get_real_macro_data()
        except:
            # 最后回退到默认数据
            from copper_macro_factors import get_default_macro_data
            return get_default_macro_data()


if __name__ == '__main__':
    # 测试整合数据收集
    print("\n" + "=" * 70)
    print("测试整合数据收集器")
    print("=" * 70 + "\n")
    
    collector = CopperMacroIntegratedCollector()
    
    # 检查 API Keys
    has_serper = bool(os.getenv('SERPER_API_KEY'))
    has_tavily = bool(os.getenv('TAVILY_API_KEY'))
    
    print(f"Serper API Key: {'✅ 已设置' if has_serper else '❌ 未设置'}")
    print(f"Tavily API Key: {'✅ 已设置' if has_tavily else '❌ 未设置'}")
    print()
    
    # 获取数据
    use_web = has_serper or has_tavily
    data = collector.get_integrated_data(use_web_search=use_web)
    
    # 打印关键指标
    print("\n📋 关键宏观指标:")
    key_indicators = [
        ('官方PMI', 'official_pmi'),
        ('财新PMI', 'caixin_pmi'),
        ('美国ISM', 'us_ism_manufacturing'),
        ('美元指数', 'dxy_index'),
        ('铜TC/RC', 'copper_tc_rc'),
        ('M1-M2剪刀差', 'm1_m2_scissors'),
    ]
    
    for name, key in key_indicators:
        value = data.get(key, 'N/A')
        print(f"  • {name}: {value}")
