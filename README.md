# 黄金价格预测系统

基于机器学习和深度学习的黄金价格预测系统，包含Web可视化界面。

## 功能特性

- **多模型集成**: LSTM、随机森林、线性回归、ARIMA
- **技术指标**: MA、EMA、MACD、RSI、布林带等
- **Web可视化**: 现代化的Web界面，实时图表展示
- **自动数据获取**: 从Yahoo Finance获取实时数据
- **未来预测**: 支持7天价格预测

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方式

### 方式一：Web应用（推荐）

```bash
python app.py
```

然后访问: http://127.0.0.1:5000

### 方式二：命令行版本

```bash
python main.py
```

或快速版本（不含LSTM）：

```bash
python quick_run.py
```

## 项目结构

```
├── app.py                  # Web应用主程序
├── main.py                 # 命令行主程序
├── quick_run.py            # 快速运行版本
├── config.py               # 配置文件
├── data_loader.py          # 数据加载和预处理
├── models.py               # 预测模型
├── visualization.py        # 可视化模块
├── requirements.txt        # 依赖列表
├── README.md               # 项目说明
├── templates/              # Web模板
│   └── index.html
├── static/                 # 静态资源
│   ├── css/style.css
│   └── js/app.js
└── output/                 # 输出目录
    ├── plots/              # 图表
    └── *.csv               # 数据文件
```

## Web界面功能

- **实时价格卡片**: 显示当前黄金价格和涨跌
- **模型性能指标**: 展示各模型的R²、RMSE等指标
- **交互式图表**:
  - 价格走势与移动平均线
  - RSI指标
  - MACD指标
  - 预测结果对比
  - 未来7天预测
- **预测表格**: 各模型未来7天预测结果
- **趋势分析**: 自动分析涨跌趋势

## 模型说明

| 模型 | 类型 | 特点 |
|------|------|------|
| LSTM | 深度学习 | 擅长捕捉长期时间依赖 |
| Random Forest | 集成学习 | 鲁棒性强，可解释性好 |
| Linear Regression | 线性模型 | 简单快速，基线模型 |
| ARIMA | 统计模型 | 经典时间序列方法 |

## 评估指标

- **RMSE**: 均方根误差
- **MAE**: 平均绝对误差
- **R²**: 决定系数
- **MAPE**: 平均绝对百分比误差

## API接口

Web应用提供以下API接口：

- `GET /api/data` - 获取价格和指标数据
- `GET /api/metrics` - 获取模型性能指标
- `GET /api/forecasts` - 获取未来预测
- `GET /api/current_price` - 获取当前价格
- `POST /api/refresh` - 刷新数据

## 注意事项

1. 需要网络连接获取数据
2. 首次运行会自动下载依赖
3. LSTM训练可能需要几分钟时间
4. 预测结果仅供参考，不构成投资建议
