# 📊 黄金预测系统 - 数据源说明

## 🥇 当日金价数据源

### 上海期货交易所 (SHFE)
- **合约**: AU2604 (主力合约)
- **备用合约**: AU2506 / AU2504 / AU2412
- **单位**: 元/克 (CNY/g)
- **获取方式**: akshare `futures_zh_daily_sina()`

---

## 📈 宏观因子数据源

### 1. ✅ 美元指数 (DXY)
- **来源**: Yahoo Finance
- **代码**: DX-Y.NYB
- **可信度**: 高
- **更新频率**: 实时

### 2. ✅ 实际利率 (TIPS)
- **来源**: TIPS ETF
- **代码**: TIP (iShares TIPS Bond ETF)
- **方法**: TIPS价格反推实际利率
- **可信度**: 高

### 3. ✅ 通胀预期 (CPI)
- **来源**: akshare
- **美国CPI**: `macro_usa_cpi()`
- **中国CPI**: `macro_china_cpi()`
- **可信度**: 高

### 4. ✅ 美债收益率
- **来源**: Yahoo Finance
- **代码**: ^TNX (10年期美债)
- **可信度**: 高

### 5. ✅ 地缘政治风险 (GPR)
- **官方来源**: Caldara-Iacoviello GPR Index
- **网址**: https://www.matteoiacoviello.com/gpr.htm
- **数据文件**: `data_gpr_daily_recent.xls`
- **可信度**: ⭐⭐⭐ 极高
- **更新频率**: 每周一
- **备用**: VIX代理指标

### 6. ✅ VIX波动率
- **来源**: Yahoo Finance
- **代码**: ^VIX
- **可信度**: 极高

### 7. ✅ 经济不确定性 (EPU)
- **官方来源**: Economic Policy Uncertainty Index
- **网址**: https://www.policyuncertainty.com/
- **中国EPU**: `China_Mainland_Paper_EPU.xlsx`
- **美国EPU**: `US_Policy_Uncertainty_Data.xlsx`
- **可信度**: ⭐⭐⭐ 极高
- **更新频率**: 月度
- **备用**: 波动率代理指标

### 8. ✅ 黄金ETF持仓
- **官方来源**: SPDR Gold Shares (GLD)
- **网址**: https://www.spdrgoldshares.com/
- **数据文件**: GLD_Daily_Holdings.xlsx
- **持仓量**: ~800-900吨
- **可信度**: ⭐⭐⭐ 极高
- **更新频率**: 每日
- **备用**: 
  - Yahoo Finance GLD计算值
  - 华安黄金ETF (518880)

### 9. ✅ 金银比/铜金比
- **来源**: akshare 上海期货交易所
- **合约**: AU2406, AG2406, CU2406
- **可信度**: 高

---

## 📁 数据缓存

所有官方数据均支持本地缓存：
- **缓存目录**: `./data_cache/`
- **GPR缓存有效期**: 24小时
- **EPU缓存有效期**: 24小时
- **ETF持仓缓存有效期**: 6小时

---

## 🔄 数据获取优先级

每个因子按以下优先级获取数据：

1. **官方数据源** (最高优先级)
   - 直接下载官方Excel/CSV文件
   - 真实度: 极高

2. **Yahoo Finance / akshare** (中等优先级)
   - API获取实时/历史数据
   - 真实度: 高

3. **计算/代理指标** (备用)
   - 基于其他数据计算得出
   - 真实度: 中

4. **默认值** (最后手段)
   - 使用历史平均值
   - 真实度: 低

---

## 📊 数据真实度统计

| 级别 | 因子数量 | 占比 | 数据源类型 |
|------|----------|------|------------|
| ⭐⭐⭐ 极高 | 5 | 56% | 官方数据 (GPR, EPU, ETF, VIX, DXY) |
| ⭐⭐ 高 | 3 | 33% | Yahoo/akshare实时数据 |
| ⭐ 中 | 1 | 11% | 计算/代理数据 (备用时) |
| ⚠️ 低 | 0 | 0% | 默认值 |

**总体真实度**: ⭐⭐⭐ 9/9因子使用真实数据

---

## 🔗 有用链接

- **GPR指数**: https://www.matteoiacoviello.com/gpr.htm
- **EPU指数**: http://www.policyuncertainty.com/
- **SPDR黄金ETF**: https://www.spdrgoldshares.com/
- **上海期货交易所**: http://www.shfe.com.cn/
- **akshare文档**: https://www.akshare.xyz/

---

## 📝 更新日志

### 2026-03-10
- ✅ 添加官方GPR数据获取 (Caldara-Iacoviello)
- ✅ 添加官方EPU数据获取 (policyuncertainty.com)
- ✅ 添加官方ETF持仓数据获取 (SPDR Gold Shares)
- ✅ 移除所有随机数，预测结果可重复
- ✅ ETF持仓权重从0恢复到0.05
