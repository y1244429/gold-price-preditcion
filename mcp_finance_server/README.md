# 金融数据 MCP 服务器

专门用于获取黄金期货、宏观数据等金融信息的 MCP (Model Context Protocol) 服务器。

## 功能特点

- 📈 上海期货交易所黄金期货数据 (AU2604/AU2506等)
- 💵 美元指数 (DXY) 数据
- 📊 美债收益率数据
- ⚡ VIX 波动率指数
- 🏆 黄金ETF持仓数据
- 🔧 技术指标计算 (RSI, MACD, 布林带)

## 安装

```bash
cd mcp_finance_server
pip install -r requirements.txt
```

## 配置使用

在 Claude Desktop 或其他 MCP 客户端中添加以下配置：

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "python",
      "args": ["/Users/ydy/CodeBuddy/20260310193311/mcp_finance_server/server.py"]
    }
  }
}
```

## 可用工具

### 1. `get_gold_futures_daily`
获取黄金期货日线数据

**参数：**
- `symbol`: 合约代码，如 "AU2604" (默认)
- `period`: 数据周期，可选 "1mo", "3mo", "6mo", "1y"

**示例：**
```json
{
  "symbol": "AU2604",
  "period": "3mo"
}
```

### 2. `get_gold_realtime_price`
获取黄金期货实时价格

**参数：**
- `symbol`: 合约代码

### 3. `get_dxy_index`
获取美元指数

**参数：**
- `period`: 数据周期

### 4. `get_us_bond_yield`
获取美国国债收益率

**参数：**
- `maturity`: 期限，"10y" 或 "2y"

### 5. `get_vix_index`
获取VIX波动率指数

### 6. `get_gold_etf_holdings`
获取黄金ETF持仓数据

### 7. `get_copper_price`
获取铜期货价格（用于铜金比计算）

### 8. `calculate_technical_indicators`
计算技术指标

**参数：**
- `prices`: 价格数组（至少20个数据点）

## 使用示例

在支持 MCP 的 AI 助手（如 Claude）中，你可以直接询问：

- "获取 AU2604 最近3个月的日线数据"
- "计算这只股票的 RSI 和 MACD 指标"
- "查询当前的美元指数和VIX"

## 数据来源

- 上海期货交易所数据：akshare
- 国际市场数据：Yahoo Finance

## 注意事项

1. 需要网络连接获取实时数据
2. 上海期货交易所数据仅在交易时间更新
3. 建议使用缓存减少API调用次数
