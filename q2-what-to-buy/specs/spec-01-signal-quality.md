# spec：对个股和 ETF 跑同一均线策略

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

`q2-what-to-buy.ipynb` 中尚未建立个股与 ETF 的对比实验。待比较对象为 5 只 A 股个股和沪深 300 ETF。本实验采用按日判断、满仓进出的均线策略，并采用 MA20 作为参数，不使用按月判断、只买不卖的均线定投。

## 任务目标

让 5 只 A 股个股和沪深 300 ETF 分别运行同一套均线策略，比较不同投资对象对应的策略表现与波动差异。

## 执行要求

1. 固定实验日期：
   - 策略回测窗口为 `SIGNAL_START = "2023-03-05"` 至 `SIGNAL_END = "2026-03-05"`。
   - 下载数据时使用 `SIGNAL_DOWNLOAD_END = "2026-03-06"`，覆盖回测结束日之后的 1 个自然日。
   - Notebook 不能使用 `pd.Timestamp.now()`、`today`、“最近 3 年”等动态日期计算。
2. 导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import SMA`
   - `from oxq.portfolio.optimizers import SignalToPositionOptimizer`
   - `from oxq.rules import ExitRule`
   - `from oxq.trade import SimBroker`
   - `from oxq.universe import StaticUniverse`
   - `pandas`、`matplotlib.pyplot`
   - 设置 `matplotlib` 中文显示支持（macOS：`Arial Unicode MS`/`STHeiti`；Windows：`SimHei`；并设置 `axes.unicode_minus = True`，使坐标轴负值使用数学减号）。
3. 使用 `YFinanceDownloader` 和 `LocalMarketDataProvider`。本书锁定版本的 `YFinanceDownloader()` 默认设置 `auto_adjust=True`，沿用第 1 章的价格口径，即继续使用调整后价格。
4. 下载沪深 300 ETF（`510300.SS`）和 5 只 A 股个股的固定窗口数据：
   - `600519.SS`（贵州茅台）
   - `000858.SZ`（五粮液）
   - `601318.SS`（中国平安）
   - `000001.SZ`（平安银行）
   - `600036.SS`（招商银行）
5. 下载调用通过 Notebook 中的 `refresh_yfinance(symbol, start, end)` 包装：
   - 下载成功时刷新本地缓存。
   - 下载失败时打印错误并继续使用本地缓存。
6. 本书配套代码所使用的 open-xquant 版本已经没有旧实验使用的 `FullPositionEntryRule`，且其中的 `Crossover` 表示一次性的上穿事件。Notebook 需要本地定义 `MovingAverageStateSignal`，按该版本的 Signal 协议复刻旧实验的均线持仓状态：
   - `name = "MovingAverageState"`。
   - `required_indicators` 指定 `sma_1` 和 `sma_20`，分别配置为 `(SMA(), {"column": "close", "period": 1})` 和 `(SMA(), {"column": "close", "period": 20})`。窗口长度通过计算参数 `period` 指定，不传给 `SMA()` 的构造函数。
   - `compute(mktdata, fast, slow)` 返回 `BUY`/`HOLD` 序列，其中 `BUY` 表示买入信号。
   - 当 `mktdata[fast] > mktdata[slow]` 时返回 `BUY`。
   - 其他时间返回 `HOLD`，退出由 `ExitRule` 处理。
7. 对每个投资对象构建一个 `Strategy`，并用 `Engine` 运行回测：
   - 在 `Strategy` 的 `signals` 中配置 `"ma_state": (MovingAverageStateSignal(), {"fast": "sma_1", "slow": "sma_20"})`，即收盘价在 MA20 上方时发出买入信号。`fast` 和 `slow` 由引擎传给该信号的 `compute()`，不传给构造函数。
   - `Strategy(..., portfolio=SignalToPositionOptimizer(signal="ma_state", buy_weight=1.0, sell_weight=0.0))`。
   - `Engine().run(..., market=provider, broker=SimBroker(), start=SIGNAL_START, end=SIGNAL_END, rules=[ExitRule(fast="sma_1", slow="sma_20")])`。
   - 用 `result.total_return()` 获取累计收益率。
   - 用 `result.annualized_volatility()` 根据策略净值的每日对数收益率计算年化波动率。
8. 画 2 张横向柱状图（上下排列，`figsize=(10, 8)`，画布大小为 10 英寸×8 英寸）：
   - 上图比较累计收益率：沪深 300 ETF 使用蓝色柱，其余 5 只个股中累计收益率为正的使用绿色柱，为负的使用红色柱。
   - 下图比较年化波动率：沪深 300 ETF 使用蓝色柱，5 只个股使用灰色柱，图题为“年化波动率对比：5 只个股与沪深 300 ETF”。

## 验收标准

1. 打印每个投资对象的回测结果，格式为 `600519.SS (贵州茅台): 累计收益率 X.XX%  年化波动率 X.XX%`。
2. 打印标题包含固定窗口：`均线策略回测结果（MA20，2023-03-05 至 2026-03-05）`。
3. 显示 2 张横向柱状图：累计收益率对比图和年化波动率对比图。
4. 根据实际运行结果打印分析，不预设收益率的正负或年化波动率的高低：
   - 打印同一策略在 5 只个股上的累计收益率最小值和最大值。
   - 打印策略在 5 只个股上的年化波动率范围，以及在沪深 300 ETF 上的年化波动率。
   - 根据实际数值，说明策略在沪深 300 ETF 上的年化波动率是低于全部个股的相应结果、高于全部个股的相应结果，还是处于个股结果的范围内。范围包含边界相等的情况。
5. 结论限定在当前样本，不得由这一次对比推导“ETF 信号更干净”“ETF 更可预测”或因果关系。
6. 说明本实验使用 open-xquant 的默认回测设置：`Engine.run()` 的 `lot_size` 默认值为 1，即最小交易单位为 1 股（份）。`SimBroker()` 未配置手续费和滑点。A 股股票和场内 ETF 实际买入通常以 100 股（份）为 1 手，因此结果只用于比较简化条件下的策略收益路径，不用于判断实际资金门槛或成交结果。
7. 按本次实际输出分析结果，不得为贴合书中图 2-1 调整实验设置或预写结论。
