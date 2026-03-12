# 数据来源标记规则

> 本规则定义铜价/金价预测系统中宏观因子数据的来源标记规范

## 1. 数据来源等级

### 1.1 三个标准等级

| 等级 | 标识 | 徽章颜色 | 数据来源 | 可信度 |
|------|------|----------|----------|--------|
| **Level 1** | 🟢 Web Search | 绿色 `#00d084` | Serper/Tavily 网络搜索 | 高 |
| **Level 2** | 🟡 API | 黄色 `#ffc107` | akshare/yfinance/其他API | 中高 |
| **Level 3** | ⚪ 模拟 | 灰色 `#adb5bd` | 默认值/估算值 | 中低 |

### 1.2 特殊等级（可选）

| 等级 | 标识 | 徽章颜色 | 使用场景 |
|------|------|----------|----------|
| **混合** | 🔵 混合 | 蓝色 `#0d6efd` | 多个来源组合 |
| **缓存** | 🟣 缓存 | 紫色 `#6f42c1` | 来自缓存数据 |
| **错误** | 🔴 错误 | 红色 `#dc3545` | 数据获取失败 |

## 2. 标记规则

### 2.1 后端标记规则

```python
@dataclass
class FactorResult:
    """宏观因子结果"""
    name: str
    value: float
    weight: float
    score: float
    data_source: str = "模拟数据"  # 必须标记数据来源
    last_updated: str = ""         # 建议添加更新时间
```

#### 数据来源判断逻辑

```python
# 规则 1: Web Search 数据优先
def determine_data_source(value: float, default_value: float, 
                          web_search_value: float = None) -> str:
    """
    判断数据来源
    
    优先级:
    1. 如果值等于 web_search 获取的值 → "Web Search"
    2. 如果值不等于默认值 → "API"
    3. 其他情况 → "模拟数据"
    """
    if web_search_value is not None and abs(value - web_search_value) < 0.01:
        return "Web Search"
    elif abs(value - default_value) > 0.01:
        return "API"
    else:
        return "模拟数据"

# 规则 2: 明确的数据源覆盖
SOURCE_PRIORITY = {
    "Web Search": 3,  # 最高优先级
    "API": 2,
    "模拟数据": 1
}
```

### 2.2 前端标记规则

```javascript
/**
 * 数据来源标记规范
 * @param {string} source - 数据来源字符串
 * @returns {string} 徽章HTML
 */
function getDataSourceBadge(source) {
    if (!source) return '<span class="badge" style="background:#6c757d">⚪ 模拟</span>';
    
    const rules = [
        { pattern: /Web Search/i, badge: '🟢 Web', color: '#00d084' },
        { pattern: /API/i, badge: '🟡 API', color: '#ffc107' },
        { pattern: /混合/i, badge: '🔵 混合', color: '#0d6efd' },
        { pattern: /缓存/i, badge: '🟣 缓存', color: '#6f42c1' },
        { pattern: /错误|失败/i, badge: '🔴 错误', color: '#dc3545' }
    ];
    
    for (const rule of rules) {
        if (rule.pattern.test(source)) {
            return `<span class="badge" style="background:${rule.color}20;color:${rule.color}">${rule.badge}</span>`;
        }
    }
    
    return '<span class="badge" style="background:#adb5bd20;color:#adb5bd">⚪ 模拟</span>';
}
```

### 2.3 CSS 样式规范

```css
/* 数据来源徽章样式 */
.data-source-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    margin-left: 8px;
}

/* 图例样式 */
.data-source-legend {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
}
```

## 3. 各因子数据源映射

### 3.1 第一层：中国实体经济

| 因子 | 默认数据源 | 优先数据源 | 降级策略 |
|------|------------|------------|----------|
| 官方PMI | 50.0 | 🟢 Web Search | → 🟡 API → ⚪ 默认 |
| 财新PMI | 50.0 | 🟡 API | → ⚪ 默认 |
| M1-M2剪刀差 | 0.0 | 🟡 API | → ⚪ 默认 |
| 社融增速 | 10.0 | 🟡 API | → ⚪ 默认 |
| 房地产新开工 | -15.0 | 🟢 Web Search | → ⚪ 默认 |
| 基建投资 | 5.0 | 🟡 API | → ⚪ 默认 |

### 3.2 第二层：美元与流动性

| 因子 | 默认数据源 | 优先数据源 | 降级策略 |
|------|------------|------------|----------|
| 美元指数(DXY) | 100.0 | 🟡 API (yfinance) | → ⚪ 默认 |
| 实际利率 | 1.5 | 🟡 API (yfinance) | → ⚪ 默认 |
| 联邦基金利率 | 5.25 | 🟢 Web Search | → ⚪ 默认 |
| 缩表进度 | 65.0 | 🟢 Web Search | → ⚪ 默认 |
| SOFR-OIS利差 | 0.15 | 🟡 API | → ⚪ 默认 |

### 3.3 第三层：全球工业周期

| 因子 | 默认数据源 | 优先数据源 | 降级策略 |
|------|------------|------------|----------|
| 美国ISM制造业 | 50.0 | 🟢 Web Search | → 🟡 API → ⚪ 默认 |
| 美国新订单 | 50.0 | 🟡 API | → ⚪ 默认 |
| 欧盟工业生产 | 0.0 | ⚪ 默认 | - |
| 全球制造业PMI | 50.0 | ⚪ 默认 | - |
| 美国库销比 | 1.3 | ⚪ 默认 | - |

### 3.4 第四层：供应与政策冲击

| 因子 | 默认数据源 | 优先数据源 | 降级策略 |
|------|------------|------------|----------|
| 铜TC/RC | -15.0 | 🟢 Web Search | → ⚪ 默认 |
| 罢工风险 | 0.0 | ⚪ 默认 | - |
| 全球库存天数 | 5.0 | ⚪ 默认 | - |
| 欧盟CBAM | 0.0 | ⚪ 默认 | - |
| 中国能耗双控 | 0.0 | ⚪ 默认 | - |

## 4. API 实现规范

### 4.1 数据来源收集器

```python
class DataSourceCollector:
    """数据源收集器基类"""
    
    SOURCE_WEB_SEARCH = "Web Search"
    SOURCE_API = "API"
    SOURCE_DEFAULT = "模拟数据"
    SOURCE_MIXED = "混合"
    SOURCE_CACHE = "缓存"
    
    def __init__(self):
        self.data_source_stats = {
            self.SOURCE_WEB_SEARCH: 0,
            self.SOURCE_API: 0,
            self.SOURCE_DEFAULT: 0
        }
    
    def tag_data_source(self, factor_name: str, value: float, 
                       source: str) -> FactorResult:
        """
        标记因子数据来源
        
        Args:
            factor_name: 因子名称
            value: 因子值
            source: 数据来源
            
        Returns:
            带标记的 FactorResult
        """
        self.data_source_stats[source] += 1
        
        return FactorResult(
            name=factor_name,
            value=value,
            data_source=source,
            # ... 其他字段
        )
    
    def get_source_coverage(self) -> Dict[str, float]:
        """获取数据源覆盖率统计"""
        total = sum(self.data_source_stats.values())
        if total == 0:
            return {}
        return {
            k: round(v / total * 100, 1) 
            for k, v in self.data_source_stats.items()
        }
```

### 4.2 数据来源验证

```python
def validate_data_source(value: float, source: str, 
                        expected_range: Tuple[float, float]) -> bool:
    """
    验证数据来源有效性
    
    Args:
        value: 数据值
        source: 声称的数据来源
        expected_range: 合理值范围
        
    Returns:
        是否通过验证
    """
    min_val, max_val = expected_range
    
    # 规则 1: 值必须在合理范围内
    if not (min_val <= value <= max_val):
        return False
    
    # 规则 2: Web Search 和 API 必须有非默认值
    if source in ["Web Search", "API"] and value == 0:
        return False
    
    return True
```

## 5. 质量检查规则

### 5.1 自动化检查

```python
def check_data_source_quality(results: List[FactorResult]) -> Dict:
    """
    检查数据来源质量
    
    返回:
        {
            "total_factors": int,
            "web_search_count": int,
            "api_count": int,
            "default_count": int,
            "real_data_percentage": float,
            "warnings": List[str]
        }
    """
    stats = {
        "total_factors": len(results),
        "web_search_count": sum(1 for r in results if "Web Search" in r.data_source),
        "api_count": sum(1 for r in results if "API" in r.data_source),
        "default_count": sum(1 for r in results if "模拟" in r.data_source),
        "warnings": []
    }
    
    stats["real_data_percentage"] = round(
        (stats["web_search_count"] + stats["api_count"]) / stats["total_factors"] * 100, 1
    )
    
    # 警告规则
    if stats["real_data_percentage"] < 30:
        stats["warnings"].append("真实数据覆盖率低于30%")
    
    if stats["web_search_count"] == 0:
        stats["warnings"].append("未使用Web Search数据")
    
    return stats
```

### 5.2 手动验证清单

- [ ] 每个因子都有明确的数据来源标记
- [ ] Web Search 数据有对应的时间戳
- [ ] API 数据有对应的 API 名称
- [ ] 默认值在合理范围内且有说明
- [ ] 数据来源覆盖率报告已生成

## 6. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-03-11 | 初始版本，定义三级标记体系 |

## 7. 相关文件

- `copper_macro_factors.py` - 后端因子计算
- `copper_macro_web_search.py` - Web Search 收集器
- `templates/gold_dashboard.html` - 前端展示
- `COPPER_MACRO_DATA_SOURCES.md` - 数据源说明
