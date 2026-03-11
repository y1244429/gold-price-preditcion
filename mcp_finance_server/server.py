#!/usr/bin/env python3
"""
金融数据 MCP 服务器
专门用于获取黄金期货、宏观数据等金融信息
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# 金融数据工具
import akshare as ak
import pandas as pd
import numpy as np
import yfinance as yf

# 创建 MCP 服务器
app = Server("finance-data-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的金融数据工具"""
    return [
        Tool(
            name="get_gold_futures_daily",
            description="获取上海期货交易所黄金期货日线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "合约代码，如 AU2604、AU2506、AU2504",
                        "default": "AU2604"
                    },
                    "period": {
                        "type": "string",
                        "description": "数据周期: 1mo(1月), 3mo(3月), 6mo(6月), 1y(1年)",
                        "default": "3mo"
                    }
                }
            }
        ),
        Tool(
            name="get_gold_realtime_price",
            description="获取黄金期货实时价格",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "合约代码，如 AU2604",
                        "default": "AU2604"
                    }
                }
            }
        ),
        Tool(
            name="get_dxy_index",
            description="获取美元指数(DXY)历史数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "数据周期: 1mo, 3mo, 6mo, 1y",
                        "default": "1mo"
                    }
                }
            }
        ),
        Tool(
            name="get_us_bond_yield",
            description="获取美国国债收益率",
            inputSchema={
                "type": "object",
                "properties": {
                    "maturity": {
                        "type": "string",
                        "description": "期限: 10y(10年期), 2y(2年期)",
                        "default": "10y"
                    }
                }
            }
        ),
        Tool(
            name="get_vix_index",
            description="获取VIX波动率指数（恐慌指数）",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "数据周期: 1mo, 3mo, 6mo",
                        "default": "1mo"
                    }
                }
            }
        ),
        Tool(
            name="get_gold_etf_holdings",
            description="获取黄金ETF持仓数据(SPDR GLD)",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "获取最近多少天的数据",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="get_copper_price",
            description="获取铜期货价格（用于铜金比计算）",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "数据周期: 1mo, 3mo, 6mo",
                        "default": "3mo"
                    }
                }
            }
        ),
        Tool(
            name="calculate_technical_indicators",
            description="计算技术指标(RSI, MACD, 布林带等)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prices": {
                        "type": "array",
                        "description": "价格数组",
                        "items": {"type": "number"}
                    }
                },
                "required": ["prices"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""
    
    if name == "get_gold_futures_daily":
        return await get_gold_futures_daily(arguments)
    elif name == "get_gold_realtime_price":
        return await get_gold_realtime_price(arguments)
    elif name == "get_dxy_index":
        return await get_dxy_index(arguments)
    elif name == "get_us_bond_yield":
        return await get_us_bond_yield(arguments)
    elif name == "get_vix_index":
        return await get_vix_index(arguments)
    elif name == "get_gold_etf_holdings":
        return await get_gold_etf_holdings(arguments)
    elif name == "get_copper_price":
        return await get_copper_price(arguments)
    elif name == "calculate_technical_indicators":
        return await calculate_technical_indicators(arguments)
    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


async def get_gold_futures_daily(arguments: dict) -> list[TextContent]:
    """获取黄金期货日线数据"""
    symbol = arguments.get("symbol", "AU2604")
    period = arguments.get("period", "3mo")
    
    try:
        # 使用akshare获取数据
        df = ak.futures_zh_daily_sina(symbol=symbol)
        
        if df is None or df.empty:
            return [TextContent(type="text", text=f"未找到 {symbol} 的数据")]
        
        # 转换列名
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['date'])
        df['Close'] = df['close'].astype(float)
        df['Open'] = df['open'].astype(float)
        df['High'] = df['high'].astype(float)
        df['Low'] = df['low'].astype(float)
        df['Volume'] = df['volume'].astype(float)
        
        # 根据period过滤数据
        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        days = days_map.get(period, 90)
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['Date'] >= cutoff_date]
        
        # 构建结果
        result = {
            "symbol": symbol,
            "data_source": "上海期货交易所",
            "record_count": len(df),
            "latest_price": round(df['Close'].iloc[-1], 2),
            "latest_date": df['Date'].iloc[-1].strftime('%Y-%m-%d'),
            "price_change_1d": round(df['Close'].iloc[-1] - df['Close'].iloc[-2], 2) if len(df) > 1 else 0,
            "data": df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(10).to_dict('records')
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取数据失败: {str(e)}")]


async def get_gold_realtime_price(arguments: dict) -> list[TextContent]:
    """获取黄金期货实时价格"""
    symbol = arguments.get("symbol", "AU2604")
    
    try:
        df = ak.futures_zh_realtime(symbol=symbol)
        
        if df is None or df.empty:
            return [TextContent(type="text", text=f"未找到 {symbol} 的实时数据")]
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data": df.to_dict('records')[0] if len(df) > 0 else {}
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取实时价格失败: {str(e)}")]


async def get_dxy_index(arguments: dict) -> list[TextContent]:
    """获取美元指数"""
    period = arguments.get("period", "1mo")
    
    try:
        dxy = yf.Ticker("DX-Y.NYB")
        hist = dxy.history(period=period)
        
        if hist.empty:
            return [TextContent(type="text", text="未找到美元指数数据")]
        
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-20] if len(hist) >= 20 else hist['Close'].iloc[0]
        change = (current - prev) / prev * 100
        
        result = {
            "index": "美元指数 (DXY)",
            "current_value": round(current, 2),
            "change_20d": round(change, 2),
            "trend": "up" if change > 0 else "down",
            "impact_on_gold": "negative",
            "note": "美元指数上涨通常对黄金价格构成压力"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取美元指数失败: {str(e)}")]


async def get_us_bond_yield(arguments: dict) -> list[TextContent]:
    """获取美国国债收益率"""
    maturity = arguments.get("maturity", "10y")
    
    try:
        symbol_map = {"10y": "^TNX", "2y": "^TWO"}
        symbol = symbol_map.get(maturity, "^TNX")
        
        bond = yf.Ticker(symbol)
        hist = bond.history(period="1mo")
        
        if hist.empty:
            return [TextContent(type="text", text="未找到美债收益率数据")]
        
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-20] if len(hist) >= 20 else hist['Close'].iloc[0]
        
        result = {
            "type": f"美国国债{maturity}收益率",
            "current_yield": round(current, 3),
            "change_20d": round(current - prev, 3),
            "impact_on_gold": "negative",
            "note": "美债收益率上升通常对黄金价格构成压力"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取美债收益率失败: {str(e)}")]


async def get_vix_index(arguments: dict) -> list[TextContent]:
    """获取VIX波动率指数"""
    period = arguments.get("period", "1mo")
    
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period=period)
        
        if hist.empty:
            return [TextContent(type="text", text="未找到VIX数据")]
        
        current = hist['Close'].iloc[-1]
        
        result = {
            "index": "VIX波动率指数",
            "current_value": round(current, 2),
            "interpretation": "恐慌" if current > 30 else "正常" if current > 20 else "低迷",
            "impact_on_gold": "positive" if current > 25 else "neutral",
            "note": "VIX上升通常利好黄金作为避险资产"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取VIX失败: {str(e)}")]


async def get_gold_etf_holdings(arguments: dict) -> list[TextContent]:
    """获取黄金ETF持仓数据"""
    days = arguments.get("days", 30)
    
    try:
        # 获取SPDR GLD数据
        gld = yf.Ticker("GLD")
        hist = gld.history(period=f"{days}d")
        
        if hist.empty:
            return [TextContent(type="text", text="未找到黄金ETF数据")]
        
        result = {
            "etf": "SPDR Gold Shares (GLD)",
            "current_price": round(hist['Close'].iloc[-1], 2),
            "period": f"{days}天",
            "trend": "up" if hist['Close'].iloc[-1] > hist['Close'].iloc[0] else "down",
            "price_change": round((hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100, 2)
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取黄金ETF数据失败: {str(e)}")]


async def get_copper_price(arguments: dict) -> list[TextContent]:
    """获取铜期货价格"""
    period = arguments.get("period", "3mo")
    
    try:
        copper = yf.Ticker("HG=F")
        hist = copper.history(period=period)
        
        if hist.empty:
            return [TextContent(type="text", text="未找到铜期货数据")]
        
        result = {
            "commodity": "铜期货",
            "current_price": round(hist['Close'].iloc[-1], 4),
            "unit": "USD/lb",
            "note": "用于计算铜金比，衡量经济周期"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取铜价失败: {str(e)}")]


async def calculate_technical_indicators(arguments: dict) -> list[TextContent]:
    """计算技术指标"""
    prices = arguments.get("prices", [])
    
    if not prices or len(prices) < 20:
        return [TextContent(type="text", text="请提供至少20个价格数据点")]
    
    try:
        prices_array = np.array(prices)
        
        # 计算RSI
        deltas = np.diff(prices_array)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-14:])
        avg_loss = np.mean(losses[-14:])
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # 计算MACD
        ema12 = pd.Series(prices_array).ewm(span=12).mean().iloc[-1]
        ema26 = pd.Series(prices_array).ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        
        # 计算布林带
        ma20 = np.mean(prices_array[-20:])
        std20 = np.std(prices_array[-20:])
        bb_upper = ma20 + 2 * std20
        bb_lower = ma20 - 2 * std20
        bb_position = (prices_array[-1] - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        result = {
            "latest_price": float(round(prices_array[-1], 2)),
            "rsi_14": float(round(rsi, 2)),
            "rsi_signal": "超买" if rsi > 70 else "超卖" if rsi < 30 else "正常",
            "macd": float(round(macd, 4)),
            "macd_signal": "看涨" if macd > 0 else "看跌",
            "bollinger_position": float(round(bb_position, 2)),
            "bb_signal": "触及上轨" if bb_position > 0.9 else "触及下轨" if bb_position < 0.1 else "中轨附近"
        }
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"计算指标失败: {str(e)}")]


async def main():
    """启动 MCP 服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
