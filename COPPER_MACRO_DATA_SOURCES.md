# 铜价四层宏观因子 - 数据来源说明

## 📊 数据收集架构

```
┌─────────────────────────────────────────────────────────────┐
│                    整合数据收集器                            │
│              (copper_macro_integrated.py)                   │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Web Search    │  │   API 数据源    │  │    默认值       │
│ (Serper/Tavily) │  │ (akshare/yfin)  │  │  (模拟数据)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔍 各层级数据来源

### 第一层：中国实体经济（40%）

| 指标 | 数据源 | 获取方式 | 更新频率 |
|------|--------|----------|----------|
| 官方制造业PMI | **Serper Web Search** | 搜索国家统计局最新发布 | 月度 |
| 财新PMI | API (akshare) | `macro_china_cx_pmi` | 月度 |
| M1-M2剪刀差 | API (akshare) | `macro_china_m2` | 月度 |
| 社融增速 | API (akshare) | `macro_china_shrz` | 月度 |
| 房地产新开工 | **Serper Web Search** | 搜索房地产统计数据 | 月度 |
| 基建投资 | API (akshare) | `macro_china_fixed_asset_investment` | 月度 |

### 第二层：美元与流动性（30%）

| 指标 | 数据源 | 获取方式 | 更新频率 |
|------|--------|----------|----------|
| 美元指数(DXY) | API (yfinance) | `DX-Y.NYB` | 实时 |
| 实际利率(TIPS) | API (yfinance) | `TIP` ETF | 实时 |
| 联邦基金利率 | 默认值 | 已知值 5.25% | 按需 |
| 缩表进度 | 默认值 | 估算值 65% | 按需 |
| SOFR-OIS利差 | 默认值 | 估算值 | 按需 |

### 第三层：全球工业周期（20%）

| 指标 | 数据源 | 获取方式 | 更新频率 |
|------|--------|----------|----------|
| 美国ISM制造业PMI | **Serper Web Search** | 搜索ISM官方发布 | 月度 |
| 美国新订单指数 | API (akshare) | `macro_usa_nym_manufacturing` | 月度 |
| 欧盟工业生产 | 默认值 | 估算值 | 季度 |
| 全球制造业PMI | 默认值 | 估算值 | 月度 |
| 美国库销比 | 默认值 | 估算值 | 月度 |

### 第四层：供应与政策冲击（10%）

| 指标 | 数据源 | 获取方式 | 更新频率 |
|------|--------|----------|----------|
| 铜TC/RC | **Serper Web Search** | 搜索铜加工费新闻 | 实时 |
| 罢工风险 | 默认值 | 新闻监控 | 事件驱动 |
| 全球库存天数 | 默认值 | LME/SHFE/COMEX估算 | 周度 |
| 欧盟CBAM | 默认值 | 政策跟踪 | 事件驱动 |
| 中国能耗双控 | 默认值 | 政策跟踪 | 事件驱动 |

## ✅ Web Search 获取的真实数据示例

```python
# 2025年3月通过 Serper Web Search 获取的最新数据
{
    'official_pmi': 50.2,           # ← Web Search 获取（比API的49.8更新）
    'us_ism_manufacturing': 50.3,   # ← Web Search 获取（比API的54.0不同）
    'copper_tc_rc': 40,             # ← Web Search 获取（美元/吨）
    'housing_starts_yoy': -19.4,    # ← Web Search 获取（房地产数据）
}
```

## 🔧 配置文件

### 环境变量设置

```bash
# 在 ~/.zshrc 或 ~/.bashrc 中添加

# Serper API Key (推荐)
# 获取地址: https://serper.dev (免费2500次/月)
export SERPER_API_KEY="your_serper_api_key_here"

# Tavily API Key (可选)
# 获取地址: https://tavily.com (免费1000次/月)
export TAVILY_API_KEY="your_tavily_api_key_here"
```

### 测试 API Key

```bash
cd /Users/ydy/CodeBuddy/20260310193311
python3 mcp_serper_config/test_serper.py
```

## 📈 数据质量对比

### 使用 Web Search 前后的对比

| 指标 | API数据 | Web Search | 差异 |
|------|---------|------------|------|
| 官方PMI | 49.8 | **50.2** | +0.4 (更乐观) |
| 美国ISM | 54.0 | **50.3** | -3.7 (更悲观) |
| 铜TC/RC | -15 | **40** | +55 (供应改善) |
| 房地产同比 | -15.0% | **-19.4%** | -4.4% (更差) |

### 数据覆盖度

- **纯模拟数据**: 0% 真实数据
- **仅API数据**: ~30% 真实数据 (PMI、ISM、铜价)
- **API + Web Search**: ~50% 真实数据 (+PMI、ISM、TC/RC、房地产)

## 🚀 使用方式

### 1. 自动模式（推荐）

系统会自动检测 API Key 并使用最优数据源：

```python
from copper_macro_factors import get_default_macro_data

data = get_default_macro_data()  # 自动选择最佳数据源
```

### 2. 手动指定

```python
from copper_macro_integrated import get_integrated_macro_data

# 强制使用 Web Search
data = get_integrated_macro_data(use_web_search=True)

# 仅使用 API
data = get_integrated_macro_data(use_web_search=False)
```

### 3. 单独使用 Web Search

```python
from copper_macro_web_search import get_web_search_macro_data

data = get_web_search_macro_data()  # 仅 Web Search 数据
```

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| `copper_macro_factors.py` | 四层宏观因子核心计算 |
| `copper_real_macro_data.py` | API数据源收集器 |
| `copper_macro_web_search.py` | Web Search收集器 |
| `copper_macro_integrated.py` | 整合收集器 |
| `mcp_serper_config/` | Serper配置目录 |

## ⚠️ 注意事项

1. **API 限制**: 
   - Serper: 2500次/月免费
   - Tavily: 1000次/月免费
   - yfinance: 有请求频率限制

2. **数据延迟**:
   - Web Search: 可能有1-2天延迟
   - API数据: 实时或当日
   - 官方统计: 月度发布

3. **数据准确性**:
   - Web Search 数据需要验证
   - 建议与官方发布对比
   - 关键决策前请人工确认

## 🔮 未来改进

- [ ] 接入更多官方数据源（国家统计局、美联储等）
- [ ] 添加数据缓存机制，减少API调用
- [ ] 实现数据历史记录和趋势分析
- [ ] 添加数据质量评分系统
