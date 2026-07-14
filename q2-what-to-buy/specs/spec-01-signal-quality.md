# Spec: 个股 vs ETF——信号质量对比

> 所有命令在沙箱外运行。

## 上下文

本章探讨"该选哪些标的"。第一步：先拿大家熟悉的个股试试 Q1 学的均线策略，看看效果如何。

## 任务

在 notebook `q2-what-to-buy.ipynb` 中，对少量 A 股个股跑均线策略并和沪深300ETF 对比，让学员直观感受个股信号的嘈杂。

## 固定实验日期

1. 策略回测窗口固定为：
   - `SIGNAL_START = "2023-03-05"`
   - `SIGNAL_END = "2026-03-05"`
2. 下载数据时使用 `SIGNAL_DOWNLOAD_END = "2026-03-06"`，覆盖回测结束日之后的一个自然日。
3. Notebook 不能使用 `pd.Timestamp.now()`、`today`、"最近 3 年"等动态日期计算。

## 要求

1. 导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import SMA`
   - `from oxq.portfolio.optimizers import SignalToPositionOptimizer`
   - `from oxq.rules import ExitRule`
   - `from oxq.trade import SimBroker`
   - `from oxq.universe import StaticUniverse`
   - pandas, matplotlib.pyplot
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）
2. 使用 `YFinanceDownloader` 和 `LocalMarketDataProvider`。
3. 下载沪深300ETF（`510300.SS`）和 5 只 A 股标的的固定窗口数据：
   - `["600519.SS", "000858.SZ", "601318.SS", "000001.SZ", "600036.SS"]`
   - 名称分别为贵州茅台、五粮液、中国平安、平安银行、招商银行。
4. 下载调用必须通过 notebook 中的 `refresh_yfinance(symbol, start, end)` 包装：
   - 下载成功时刷新本地缓存。
   - 下载失败时打印错误并继续使用本地缓存。
5. 当前 SDK 已没有旧实验使用的 `FullPositionEntryRule`，且当前 `Crossover` 表示一次性的上穿事件。Notebook 需要本地定义 `MovingAverageStateSignal`，用当前 SDK 的 Signal 协议复刻旧实验的均线持仓状态：
   - `name = "MovingAverageState"`。
   - `required_indicators` 指定 `sma_1` 和 `sma_20`。
   - `compute(mktdata, fast, slow)` 返回 `BUY/HOLD` 序列。
   - 当 `mktdata[fast] > mktdata[slow]` 时返回 `BUY`。
   - 其他时间返回 `HOLD`，退出由 `ExitRule` 处理。
6. 对每个标的（5 只个股 + 沪深300ETF），构建一个 `Strategy` 并用 `Engine` 运行回测：
   - 信号：`MovingAverageStateSignal(fast="sma_1", slow="sma_20")`，即收盘价在 20 日均线上方时持有。
   - `Strategy(..., portfolio=SignalToPositionOptimizer(signal="ma_state", buy_weight=1.0, sell_weight=0.0))`。
   - `Engine().run(..., market=provider, broker=SimBroker(), start=SIGNAL_START, end=SIGNAL_END, rules=[ExitRule(fast="sma_1", slow="sma_20")])`。
   - 用 `result.total_return()` 获取收益率。
   - 用 `result.annualized_volatility()` 获取年化波动率。
7. 画两张横向柱状图（上下排列，figsize 10×8）：
   - 第一张：收益率对比，沪深300ETF 用蓝色高亮，其余按正负区分绿色/红色。
   - 第二张：年化波动率对比，沪深300ETF 用蓝色，个股用灰色。

## 结果呈现

1. 打印每只标的的回测结果，格式：`600519.SS (贵州茅台): 收益率 X.XX%  年化波动率 X.XX%`。
2. 打印标题必须包含固定窗口：`均线策略回测结果（20日均线，2023-03-05 至 2026-03-05）`。
3. 两张横向柱状图（收益率 + 年化波动率）。
4. 打印分析：
   - 「同样的均线策略，5 只个股的结果天差地别——从大幅盈利到严重亏损都有。」
   - 「再看波动率：个股年化波动率在 XX%-XX%，而沪深300ETF 只有 XX%——300 只股票的噪音互相抵消，波动被分散掉了。」
   - 「组合能对抗波动。ETF 就是一种组合。」
