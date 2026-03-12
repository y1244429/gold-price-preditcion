"""
使用 Web Search (Serper/Tavily) 获取铜价宏观数据
通过搜索获取最新的宏观经济指标
"""

import os
import json
import requests
from typing import Dict, Optional
from datetime import datetime

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass


class CopperMacroWebSearch:
    """使用 Web Search API 获取铜价宏观数据"""
    
    def __init__(self):
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        
    def search_with_serper(self, query: str, num_results: int = 5) -> Optional[Dict]:
        """使用 Serper API 搜索"""
        if not self.serper_api_key or self.serper_api_key == 'your_api_key_here':
            print("⚠️ SERPER_API_KEY 未设置")
            return None
        
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": num_results,
            "gl": "cn",
            "hl": "zh-cn"
        })
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Serper API 错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Serper 请求失败: {e}")
            return None
    
    def search_with_tavily(self, query: str, num_results: int = 5) -> Optional[Dict]:
        """使用 Tavily API 搜索"""
        if not self.tavily_api_key:
            print("⚠️ TAVILY_API_KEY 未设置")
            return None
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "max_results": num_results,
            "search_depth": "basic",
            "include_answer": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Tavily API 错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Tavily 请求失败: {e}")
            return None
    
    def get_china_pmi_data(self) -> Dict:
        """获取中国 PMI 数据"""
        data = {}
        
        # 使用 Serper 搜索
        print("🔍 搜索中国 PMI 数据...")
        search_query = "中国制造业PMI 2025年2月 国家统计局"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                print(f"  📰 {item.get('title', '')}")
                # 尝试从摘要中提取 PMI 数值
                import re
                pmi_match = re.search(r'(\d{2}\.\d)', snippet)
                if pmi_match:
                    pmi_value = float(pmi_match.group(1))
                    if 40 <= pmi_value <= 60:
                        data['official_pmi'] = pmi_value
                        print(f"  ✅ 找到官方PMI: {pmi_value}")
                        break
        
        # 使用 Tavily 搜索（如果 Serper 失败）
        if 'official_pmi' not in data:
            print("  🔄 尝试 Tavily...")
            result = self.search_with_tavily(search_query)
            if result and 'answer' in result:
                answer = result['answer']
                import re
                pmi_match = re.search(r'(\d{2}\.\d)', answer)
                if pmi_match:
                    pmi_value = float(pmi_match.group(1))
                    if 40 <= pmi_value <= 60:
                        data['official_pmi'] = pmi_value
                        print(f"  ✅ Tavily 找到官方PMI: {pmi_value}")
        
        return data
    
    def get_us_ism_pmi(self) -> Dict:
        """获取美国 ISM 制造业 PMI"""
        data = {}
        
        print("🔍 搜索美国 ISM PMI 数据...")
        search_query = "US ISM Manufacturing PMI February 2025"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                import re
                # 匹配 ISM PMI 数值
                pmi_match = re.search(r'(\d{2}\.\d|\d{2})', snippet)
                if pmi_match:
                    pmi_value = float(pmi_match.group(1))
                    if 40 <= pmi_value <= 70:
                        data['us_ism_manufacturing'] = pmi_value
                        print(f"  ✅ 找到美国ISM: {pmi_value}")
                        break
        
        return data
    
    def get_copper_tc_rc(self) -> Dict:
        """获取铜 TC/RC 数据"""
        data = {}
        
        print("🔍 搜索铜 TC/RC 数据...")
        search_query = "铜精矿 TC RC 加工费 2025年2月"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                print(f"  📰 {item.get('title', '')[:50]}...")
                # TC/RC 通常在 20-100 美元/吨范围
                import re
                tc_match = re.search(r'(\d{2,3})[^\d]*美元', snippet)
                if tc_match:
                    tc_value = int(tc_match.group(1))
                    if 10 <= tc_value <= 200:
                        data['copper_tc_rc'] = tc_value
                        print(f"  ✅ 找到铜TC/RC: {tc_value} 美元/吨")
                        break
        
        return data
    
    def get_china_real_estate(self) -> Dict:
        """获取中国房地产数据"""
        data = {}
        
        print("🔍 搜索中国房地产数据...")
        search_query = "中国房地产新开工面积 同比 2025年"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                import re
                # 匹配同比变化百分比
                yoy_match = re.search(r'([-\d\.]+)%', snippet)
                if yoy_match:
                    yoy_value = float(yoy_match.group(1))
                    if -50 <= yoy_value <= 50:
                        data['housing_starts_yoy'] = yoy_value
                        print(f"  ✅ 找到房地产同比: {yoy_value}%")
                        break
        
        return data
    
    def get_fed_policy_data(self) -> Dict:
        """获取美联储政策数据 - 利率和缩表进度"""
        data = {}
        
        # 1. 搜索美联储利率决议 (使用英文更准确)
        print("🔍 搜索美联储利率决议...")
        search_queries = [
            "Federal Reserve interest rate 2025 current target",
            "Fed funds rate March 2025 FOMC"
        ]
        
        import re
        for search_query in search_queries:
            result = self.search_with_serper(search_query)
            if result and 'organic' in result:
                for item in result['organic'][:3]:
                    snippet = item.get('snippet', '')
                    title = item.get('title', '')
                    print(f"  📰 {title[:50]}...")
                    
                    # 匹配利率区间 (如 4.25%-4.50%, 4.25% - 4.50%)
                    rate_match = re.search(r'(\d+\.\d+)%?\s*-\s*(\d+\.\d+)%?', snippet)
                    if rate_match:
                        rate_low = float(rate_match.group(1))
                        rate_high = float(rate_match.group(2))
                        # 验证合理范围 (当前应该在 4.0-5.5% 之间)
                        if 4.0 <= rate_low <= 5.5 and 4.0 <= rate_high <= 5.5:
                            fed_rate = (rate_low + rate_high) / 2
                            data['fed_funds_rate'] = fed_rate
                            print(f"  ✅ 找到联邦基金利率区间: {rate_low}%-{rate_high}%")
                            break
                if 'fed_funds_rate' in data:
                    break
        
        # 2. 搜索美联储缩表进度
        print("🔍 搜索美联储缩表进度...")
        search_query = "Federal Reserve balance sheet QT taper 2025"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                # 查找资产负债表规模
                balance_match = re.search(r'(\d+\.?\d*)\s*(trillion|tn)', snippet, re.IGNORECASE)
                if balance_match:
                    balance = float(balance_match.group(1))
                    print(f"  ✅ 找到资产负债表规模: {balance} trillion")
                    # 估算缩表进度: 峰值约8.9万亿, 目标约6.5万亿
                    peak = 8.9
                    target = 6.5
                    if balance <= peak:
                        progress = min(100, max(0, (peak - balance) / (peak - target) * 100))
                        data['qt_progress'] = round(progress, 1)
                        print(f"  ✅ 估算缩表进度: {data['qt_progress']}%")
                    break
        
        # 3. 搜索美元指数
        print("🔍 搜索美元指数 DXY...")
        search_query = "US Dollar Index DXY today current level"
        
        result = self.search_with_serper(search_query)
        if result and 'organic' in result:
            for item in result['organic'][:3]:
                snippet = item.get('snippet', '')
                # 匹配DXY数值 (通常在 100-110 范围)
                dxy_match = re.search(r'(10[0-9]\.\d{2})', snippet)
                if dxy_match:
                    dxy_value = float(dxy_match.group(1))
                    if 100 <= dxy_value <= 110:
                        data['dxy_index'] = dxy_value
                        print(f"  ✅ 找到美元指数: {dxy_value}")
                        break
        
        return data
    
    def get_all_web_data(self) -> Dict:
        """获取所有 Web 搜索数据"""
        print("=" * 70)
        print("🌐 使用 Web Search 获取铜价宏观数据")
        print("=" * 70)
        
        all_data = {}
        
        # 检查 API Keys
        if not self.serper_api_key and not self.tavily_api_key:
            print("\n❌ 错误: 未设置 SERPER_API_KEY 或 TAVILY_API_KEY")
            print("   请设置环境变量:")
            print("   export SERPER_API_KEY=your_key")
            print("   export TAVILY_API_KEY=your_key")
            print("\n   获取 API Key:")
            print("   - Serper: https://serper.dev (免费2500次/月)")
            print("   - Tavily: https://tavily.com (免费1000次/月)")
            return all_data
        
        # 获取各类数据
        all_data.update(self.get_china_pmi_data())
        all_data.update(self.get_us_ism_pmi())
        all_data.update(self.get_copper_tc_rc())
        all_data.update(self.get_china_real_estate())
        all_data.update(self.get_fed_policy_data())  # 新增美联储政策数据
        
        print("\n" + "=" * 70)
        print("📊 Web Search 数据获取完成")
        print(f"   获取到 {len(all_data)} 个数据点")
        print("=" * 70)
        
        return all_data
    
    def print_data_summary(self, data: Dict):
        """打印数据摘要"""
        print("\n获取到的真实数据:")
        for key, value in data.items():
            print(f"  • {key}: {value}")


# 便捷函数
def get_web_search_macro_data() -> Dict:
    """使用 Web Search 获取宏观数据的便捷函数"""
    collector = CopperMacroWebSearch()
    data = collector.get_all_web_data()
    collector.print_data_summary(data)
    return data


if __name__ == '__main__':
    # 测试 Web Search 数据收集
    data = get_web_search_macro_data()
    
    # 与现有数据对比
    if data:
        print("\n\n与现有数据对比:")
        from copper_real_macro_data import CopperRealMacroDataCollector
        
        real_collector = CopperRealMacroDataCollector()
        real_data = real_collector.get_all_real_data()
        
        for key in ['official_pmi', 'us_ism_manufacturing', 'copper_tc_rc']:
            if key in data:
                web_value = data[key]
                real_value = real_data.get(key, 'N/A')
                print(f"  {key}:")
                print(f"    Web Search: {web_value}")
                print(f"    API获取: {real_value}")
