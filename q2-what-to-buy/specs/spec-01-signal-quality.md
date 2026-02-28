# Spec: 个股 vs ETF——信号质量对比

> 所有命令在沙箱外运行。

## 上下文

本章探讨"该选哪些标的"。第一步：先拿大家熟悉的个股试试 Q1 学的均线策略，看看效果如何。

## 任务

在 notebook `q2-what-to-buy.ipynb` 中新建代码单元格，对少量 A 股个股跑均线策略并和沪深300ETF 对比，让学员直观感受个股信号的嘈杂。

## 要求

1. 在 notebook 中新建代码单元格
2. 导入所需库并设置中文显示：
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - pandas, matplotlib.pyplot, numpy
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）
3. 使用 `YFinanceDownloader` 和 `LocalMarketDataProvider`
4. 下载沪深300ETF（`510300.SS`）最近 3 年数据（起始日期为 3 年前，结束日期为当天）
5. 下载 5 只 A 股标的最近 3 年数据：`["600519.SS", "000858.SZ", "601318.SS", "000001.SZ", "600036.SS"]`（茅台、五粮液、中国平安、平安银行、招商银行）
6. 实现一个简单的均线策略回测函数 `simple_ma_backtest(bars, ma_period=20)`：
   - 输入：open-xquant 返回的 DataFrame（含 close 列）
   - 计算 N 日均线
   - 规则：收盘价上穿均线买入，下穿均线卖出
   - 返回最终收益率
7. 对 5 只个股 + 沪深300ETF 分别运行回测
8. 画一张横向柱状图（figsize 10×5）：6 个标的的收益率对比，沪深300ETF 用蓝色高亮，其余按正负区分绿色/红色

## 结果呈现

1. 打印每只标的的回测结果，格式：`600519.SS (贵州茅台): 收益率 X.XX%`
2. 横向柱状图
3. 打印分析：
   - 「同样的均线策略，5 只个股的结果天差地别——从大幅盈利到严重亏损都有。」
   - 「单只股票波动大、不可预测，但沪深300ETF 包含 300 只股票，个股的噪音互相抵消，表现更稳定。」
   - 「组合能对抗波动。ETF 就是一种组合。」
