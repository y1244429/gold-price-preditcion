/**
 * 黄金价格预测系统 - 前端逻辑
 */

// 全局变量
let mainChart, rsiChart, macdChart, comparisonChart;
let chartData = {};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
});

// 加载所有数据
async function loadAllData() {
    try {
        showToast('正在加载数据...');
        
        // 并行加载所有数据
        await Promise.all([
            loadCurrentPrice(),
            loadMetrics(),
            loadChartData(),
            loadForecasts(),
            loadPredictions()
        ]);
        
        showToast('数据加载完成!');
    } catch (error) {
        console.error('加载数据失败:', error);
        showToast('数据加载失败，请重试', 'error');
    }
}

// 加载当前价格
async function loadCurrentPrice() {
    try {
        const response = await fetch('/api/current_price');
        const data = await response.json();
        
        if (data.error) return;
        
        document.getElementById('currentPrice').textContent = `$${data.price.toLocaleString()}`;
        document.getElementById('priceDate').textContent = `更新于: ${data.date}`;
        
        const changeEl = document.getElementById('priceChange');
        const isUp = data.change >= 0;
        changeEl.className = `price-change ${isUp ? 'change-up' : 'change-down'}`;
        changeEl.innerHTML = `
            <span class="change-value">${isUp ? '+' : ''}${data.change.toFixed(2)}</span>
            <span class="change-percent">(${isUp ? '+' : ''}${data.change_pct.toFixed(2)}%)</span>
        `;
    } catch (error) {
        console.error('加载价格失败:', error);
    }
}

// 加载模型指标
async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const metrics = await response.json();
        
        const grid = document.getElementById('metricsGrid');
        grid.innerHTML = '';
        
        const modelColors = {
            'Random Forest': '#22c55e',
            'Linear Regression': '#3b82f6',
            'ARIMA': '#f59e0b',
            'LSTM': '#a855f7'
        };
        
        for (const [name, metric] of Object.entries(metrics)) {
            const card = document.createElement('div');
            card.className = 'metric-card';
            card.innerHTML = `
                <div class="metric-title">${name}</div>
                <div class="metric-value" style="color: ${modelColors[name] || '#FFD700'}">
                    R²: ${metric.R2.toFixed(4)}
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                    RMSE: $${metric.RMSE.toFixed(2)}<br>
                    MAE: $${metric.MAE.toFixed(2)}<br>
                    MAPE: ${metric.MAPE.toFixed(2)}%
                </div>
            `;
            grid.appendChild(card);
        }
    } catch (error) {
        console.error('加载指标失败:', error);
    }
}

// 加载图表数据
async function loadChartData() {
    try {
        const response = await fetch('/api/data');
        chartData = await response.json();
        
        // 初始化所有图表
        initMainChart();
        initRsiChart();
        initMacdChart();
    } catch (error) {
        console.error('加载图表数据失败:', error);
    }
}

// 加载预测数据
async function loadForecasts() {
    try {
        const response = await fetch('/api/forecasts');
        const data = await response.json();
        
        updateForecastTable(data);
        initComparisonChart();
    } catch (error) {
        console.error('加载预测失败:', error);
    }
}

// 加载历史预测
async function loadPredictions() {
    try {
        const response = await fetch('/api/predictions');
        const data = await response.json();
        window.predictionsData = data.predictions;
    } catch (error) {
        console.error('加载预测对比失败:', error);
    }
}

// 初始化主图表
function initMainChart() {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    if (mainChart) {
        mainChart.destroy();
    }
    
    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [
                {
                    label: '收盘价',
                    data: chartData.prices,
                    borderColor: '#FFD700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'MA20',
                    data: chartData.ma20,
                    borderColor: '#3b82f6',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.4
                },
                {
                    label: 'MA60',
                    data: chartData.ma60,
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    labels: { color: '#a0a0b0' }
                },
                tooltip: {
                    backgroundColor: 'rgba(20, 20, 25, 0.9)',
                    titleColor: '#FFD700',
                    bodyColor: '#ffffff',
                    borderColor: '#2a2a3a',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(42, 42, 58, 0.5)' },
                    ticks: { color: '#a0a0b0' }
                },
                y: {
                    grid: { color: 'rgba(42, 42, 58, 0.5)' },
                    ticks: { color: '#a0a0b0' }
                }
            }
        }
    });
}

// 初始化RSI图表
function initRsiChart() {
    const ctx = document.getElementById('rsiChart').getContext('2d');
    
    if (rsiChart) {
        rsiChart.destroy();
    }
    
    rsiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [{
                label: 'RSI',
                data: chartData.rsi,
                borderColor: '#a855f7',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: {
                        overbought: {
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: 'rgba(239, 68, 68, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        oversold: {
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: 'rgba(34, 197, 94, 0.5)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(42, 42, 58, 0.5)' },
                    ticks: { color: '#a0a0b0' }
                }
            }
        }
    });
}

// 初始化MACD图表
function initMacdChart() {
    const ctx = document.getElementById('macdChart').getContext('2d');
    
    if (macdChart) {
        macdChart.destroy();
    }
    
    macdChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [{
                label: 'MACD',
                data: chartData.macd,
                borderColor: '#3b82f6',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    grid: { color: 'rgba(42, 42, 58, 0.5)' },
                    ticks: { color: '#a0a0b0' }
                }
            }
        }
    });
}

// 初始化对比图表
function initComparisonChart() {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    
    if (comparisonChart) {
        comparisonChart.destroy();
    }
    
    // 获取指标数据
    fetch('/api/metrics').then(r => r.json()).then(metrics => {
        const labels = Object.keys(metrics);
        const rmseData = labels.map(m => metrics[m].RMSE);
        const r2Data = labels.map(m => metrics[m].R2);
        
        comparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'RMSE',
                        data: rmseData,
                        backgroundColor: 'rgba(59, 130, 246, 0.7)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'R²',
                        data: r2Data,
                        backgroundColor: 'rgba(255, 215, 0, 0.7)',
                        borderColor: '#FFD700',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#a0a0b0' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#a0a0b0' },
                        grid: { display: false }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'RMSE', color: '#3b82f6' },
                        ticks: { color: '#a0a0b0' },
                        grid: { color: 'rgba(42, 42, 58, 0.5)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'R²', color: '#FFD700' },
                        ticks: { color: '#a0a0b0' },
                        grid: { display: false },
                        min: 0,
                        max: 1
                    }
                }
            }
        });
    });
}

// 更新预测表格
function updateForecastTable(data) {
    const tbody = document.querySelector('#forecastTable tbody');
    tbody.innerHTML = '';
    
    // 计算集成预测
    const models = Object.keys(data.predictions);
    const days = data.predictions[models[0]].length;
    
    for (let i = 0; i < days; i++) {
        const row = document.createElement('tr');
        
        // 日期
        row.innerHTML = `<td>${data.dates[i]}</td>`;
        
        // 各模型预测
        const values = [];
        models.forEach(model => {
            const val = data.predictions[model][i];
            values.push(val);
            row.innerHTML += `<td>$${val.toFixed(2)}</td>`;
        });
        
        // 填充缺失的模型列
        for (let j = models.length; j < 4; j++) {
            row.innerHTML += `<td>-</td>`;
        }
        
        // 集成预测
        const ensemble = values.reduce((a, b) => a + b, 0) / values.length;
        row.innerHTML += `<td class="highlight">$${ensemble.toFixed(2)}</td>`;
        
        tbody.appendChild(row);
    }
    
    // 更新趋势分析
    const firstDay = data.predictions[models[0]][0];
    const lastDay = data.predictions[models[0]][days - 1];
    const allValues = models.flatMap(m => data.predictions[m]);
    const avgForecast = allValues.reduce((a, b) => a + b, 0) / allValues.length;
    
    const change = lastDay - firstDay;
    const changePct = (change / firstDay) * 100;
    
    let trendText, trendClass;
    if (changePct > 2) {
        trendText = `强烈看涨 📈 (+${changePct.toFixed(2)}%)`;
        trendClass = 'change-up';
    } else if (changePct > 0.5) {
        trendText = `看涨 ↑ (+${changePct.toFixed(2)}%)`;
        trendClass = 'change-up';
    } else if (changePct < -2) {
        trendText = `强烈看跌 📉 (${changePct.toFixed(2)}%)`;
        trendClass = 'change-down';
    } else if (changePct < -0.5) {
        trendText = `看跌 ↓ (${changePct.toFixed(2)}%)`;
        trendClass = 'change-down';
    } else {
        trendText = `横盘震荡 → (${changePct.toFixed(2)}%)`;
        trendClass = '';
    }
    
    document.getElementById('forecastSummary').innerHTML = `
        <span class="trend-indicator ${trendClass}">${trendText}</span>
        <span style="margin-left: 15px; color: var(--text-secondary);">
            平均预测: $${avgForecast.toFixed(2)}
        </span>
    `;
}

// 显示不同图表
function showChart(type) {
    // 更新按钮状态
    document.querySelectorAll('.chart-controls .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (type === 'price') {
        initMainChart();
    } else if (type === 'prediction' && window.predictionsData) {
        showPredictionChart();
    } else if (type === 'forecast') {
        showForecastChart();
    }
}

// 显示预测对比图表
function showPredictionChart() {
    if (!window.predictionsData) return;
    
    const dates = chartData.dates.slice(-Object.values(window.predictionsData)[0].length);
    const datasets = [
        {
            label: '实际价格',
            data: chartData.prices.slice(-dates.length),
            borderColor: '#ffffff',
            borderWidth: 2,
            pointRadius: 0
        }
    ];
    
    const colors = ['#22c55e', '#3b82f6', '#f59e0b', '#a855f7'];
    let i = 0;
    for (const [name, pred] of Object.entries(window.predictionsData)) {
        datasets.push({
            label: name,
            data: pred,
            borderColor: colors[i % colors.length],
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0
        });
        i++;
    }
    
    mainChart.data.labels = dates;
    mainChart.data.datasets = datasets;
    mainChart.update();
}

// 显示未来预测图表
function showForecastChart() {
    fetch('/api/forecasts').then(r => r.json()).then(data => {
        // 获取最近30天历史数据
        const historyDates = chartData.dates.slice(-30);
        const historyPrices = chartData.prices.slice(-30);
        
        const datasets = [{
            label: '历史价格',
            data: [...historyPrices, ...Array(data.dates.length).fill(null)],
            borderColor: '#ffffff',
            borderWidth: 2,
            pointRadius: 0
        }];
        
        const colors = ['#22c55e', '#3b82f6', '#f59e0b', '#a855f7'];
        let i = 0;
        
        for (const [name, pred] of Object.entries(data.predictions)) {
            datasets.push({
                label: name,
                data: [...Array(historyDates.length - 1).fill(null), historyPrices[historyPrices.length - 1], ...pred],
                borderColor: colors[i % colors.length],
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 3
            });
            i++;
        }
        
        mainChart.data.labels = [...historyDates, ...data.dates];
        mainChart.data.datasets = datasets;
        mainChart.update();
    });
}

// 刷新数据
async function refreshData() {
    try {
        showToast('正在刷新数据...');
        
        const response = await fetch('/api/refresh', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            await loadAllData();
            showToast('数据刷新成功!');
        } else {
            showToast('刷新失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('刷新失败:', error);
        showToast('刷新失败，请重试', 'error');
    }
}

// 显示提示
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    
    toastMessage.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 更新时间
function updateTime() {
    document.getElementById('updateTime').textContent = new Date().toLocaleString('zh-CN');
}

updateTime();
