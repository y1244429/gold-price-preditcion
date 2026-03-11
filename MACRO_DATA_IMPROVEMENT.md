# 宏观数据质量改进报告

## 改进概述

针对宏观预测数据质量的问题，实施了以下改进措施：

### 1. 优先使用 akshare 数据源

将原本依赖 Yahoo Finance 的数据源改为优先使用 akshare：

| 因子 | 改进前 | 改进后 |
|------|--------|--------|
| **美元指数** | Yahoo Finance DXY | akshare 中国银行外汇牌价 |
| **实际利率** | TIPS ETF | akshare 中国国债收益率 - CPI |
| **美债收益率** | Yahoo Finance ^TNX | akshare 中美利率对比数据 |
| **VIX波动率** | Yahoo Finance ^VIX | akshare 上证指数波动率 |

### 2. 集成 Serper MCP 作为备用

当 Yahoo Finance 限流时，使用 Serper API 搜索数据：
- 黄金价格搜索
- 美元强弱间接估算

### 3. 确保官方 GPR/EPU 数据源

- **GPR**: Caldara-Iacoviello 地缘政治风险指数
  - 官方数据源: https://www.matteoiacoviello.com/gpr.htm
  - 备用: 缓存数据 → VIX代理
  
- **EPU**: Economic Policy Uncertainty 指数
  - 官方数据源: https://www.policyuncertainty.com/
  - 中国EPU和美国EPU双源备份
  - 备用: 缓存数据 → 波动率代理

### 4. 增强 ETF 持仓数据获取

- 优先: SPDR Gold Shares 官方持仓数据
- 备用1: Yahoo Finance GLD 计算值
- 备用2: 华安黄金ETF (518880)

## 数据源优先级架构

```
宏观因子数据获取优先级:

1. 美元指数 (DXY)
   ├── akshare 中国银行外汇牌价 (USD/CNY)
   ├── Yahoo Finance DX-Y.NYB
   └── Serper API (黄金价格间接估算)

2. 实际利率 (TIPS)
   ├── akshare 中国国债收益率 - CPI
   ├── akshare 美国国债收益率
   ├── TIPS ETF (^TIP)
   └── 盈亏平衡通胀率

3. 通胀预期 (CPI)
   ├── akshare macro_usa_cpi()
   ├── akshare macro_china_cpi()
   └── 盈亏平衡通胀率

4. 美债收益率
   ├── akshare bond_zh_us_rate()
   └── Yahoo Finance ^TNX

5. 地缘政治风险 (GPR)
   ├── enhanced_gpr_epu.py 官方数据
   ├── 缓存数据
   └── VIX代理

6. VIX波动率
   ├── akshare 上证指数波动率
   ├── akshare 50ETF波动率
   └── Yahoo Finance ^VIX

7. 经济不确定性 (EPU)
   ├── enhanced_gpr_epu.py 中国EPU
   ├── enhanced_gpr_epu.py 美国EPU
   ├── 缓存数据
   └── 波动率代理

8. 黄金ETF持仓
   ├── etf_holdings_collector.py SPDR官方
   ├── Yahoo Finance GLD计算
   └── 华安黄金ETF

9. 金银比/铜金比
   └── akshare 上期所 (保持原样)
```

## 预期改进效果

### 改进前
- 真实数据: ~30%
- 代理数据: ~22%
- 模拟数据: ~48%

### 改进后
- 真实数据: 60-80%
- 代理数据: 10-20%
- 模拟数据: 0-20%

## 文件修改清单

1. **gold_app.py**
   - `get_dxy()`: 添加 akshare 和 Serper 备用
   - `get_real_rate_tips()`: 添加 akshare 中国国债数据
   - `get_bond_yield()`: 添加 akshare 中美利率数据
   - `get_vix()`: 添加 akshare 中国波动率数据
   - `get_gpr()`: 增强官方数据源优先级
   - `get_epu()`: 增强官方数据源优先级
   - `get_etf_holdings()`: 增强官方数据源优先级

2. **enhanced_gpr_epu.py** (保持原样)
   - 官方GPR/EPU数据获取
   - 缓存机制

3. **etf_holdings_collector.py** (保持原样)
   - SPDR官方数据获取
   - 华安ETF数据获取

4. **serper_data_source.py** (保持原样)
   - Serper API 黄金价格搜索

## 运行测试

```bash
python test_enhanced_macro.py
```

## 后续建议

1. **定期更新缓存**: 设置定时任务更新 GPR/EPU 缓存数据
2. **监控数据质量**: 使用 check_macro_data_quality.py 定期检查
3. **扩展数据源**: 考虑添加更多国内数据源（如Wind、东方财富）
4. **异常处理**: 增加更多数据验证和异常处理逻辑
