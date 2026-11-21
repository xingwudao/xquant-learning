# spec：再平衡间隔——多久调整一次才合适？

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

当前基础配置采用简化风险平价权重分配方法，在 20 日滚动波动率形成有效值后持有沪深 300 ETF、纳指 100 ETF 和黄金 ETF，并每 10 个交易日再平衡一次。当前需要检查改变再平衡间隔会怎样影响策略表现和交易成本。

## 任务目标

比较不同再平衡间隔的效果，并首次引入交易成本。

## 执行要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.trade.PercentageFee`
   - `oxq.trade.SimBroker`（重点关注 `fee_model` 参数）
   - `oxq.rules.RebalanceFrequencyRule`
   - `oxq.portfolio.optimizers.RiskParityOptimizer`
   - `oxq.core.Engine`（重点关注 `run(rules=[...])` 参数）、`oxq.core.Strategy`

3. 创建 Notebook `q4-when-to-trade.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility`
   - `from oxq.signals import Threshold`
   - `from oxq.portfolio.optimizers import RiskParityOptimizer`
   - `from oxq.rules import RebalanceFrequencyRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - `pandas`、`numpy`、`matplotlib.pyplot`、`Decimal`
   - 设置 `matplotlib` 中文显示支持（macOS：Arial Unicode MS/STHeiti；Windows：SimHei；`axes.unicode_minus = True`，使坐标轴负值使用数学减号）

4. 复用第 3 章的日线行情数据、标的池和简化风险平价配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深 300 ETF", "513100.SS": "纳指 100 ETF", "518880.SS": "黄金 ETF"}`
   - 数据起始日期 `START = "2021-01-01"`
   - 数据结束日期 `END = "2026-03-18"`，不要使用 `today`、`now`，也不要让 open-xquant 自动采用最新日期
   - `yfinance` 的 `end` 参数是排他边界，下载时使用 `DOWNLOAD_END = "2026-03-19"`，读取和回测统一使用 `END`
   - 使用 `YFinanceDownloader` 下载数据。下载失败时打印提示并继续使用本地缓存，避免离线复跑失败
   - 构建 `StaticUniverse`，加载数据
   - 计算 `common_trading_days` 交集，后续画图时净值曲线按共同交易日对齐，避免个别日期数据缺失造成错位。3 只 ETF 均在上交所交易，不把这种日期差异写成中美交易日历差异
   - 定义 `BookCompatibleSimBroker(SimBroker)`：锁定版本的 `SimBroker` 会因为“买入金额+手续费”超过现金而拒单。本书原实验设定是手续费扣绩效，但不让手续费改变再平衡成交集合，因此覆盖 `set_available_cash`，在计入手续费的回测中使用这个兼容模拟券商。须明确这可能使现金余额短暂为负，不等同于真实账户的资金约束，只用于隔离观察手续费影响
   - 创建 `Threshold` 信号并绑定所需指标：
     ```python
     signal = Threshold()
     signal.required_indicators = {"vol": (RollingVolatility(), {"column": "close", "period": 20})}
     ```
   - 创建 `RiskParityOptimizer`：`portfolio = RiskParityOptimizer(volatility_col="vol")`

5. 定义 `run_backtest(frequency, fee_model, order_rules)` 辅助函数，封装策略构建和回测执行，供后续 spec 复用：
   ```python
   def run_backtest(frequency, fee_model=None, order_rules=None):
       signal = Threshold()
       signal.required_indicators = {
           "vol": (RollingVolatility(), {"column": "close", "period": 20}),
       }
       strategy = Strategy(
           name=f"freq-{frequency}",
           universe=universe,
           signals={"active": (signal, {"column": "close", "threshold": 0, "relationship": "gt"})},
           portfolio=RiskParityOptimizer(volatility_col="vol"),
       )
       rules = [RebalanceFrequencyRule(interval_days=frequency)]
       if order_rules:
           rules.extend(order_rules)
       broker = BookCompatibleSimBroker(fee_model=fee_model) if fee_model else SimBroker()
       return Engine().run(
           strategy,
           market=LocalMarketDataProvider(),
           broker=broker,
           start=START,
           end=END,
           rules=rules,
       )
   ```

6. 定义 4 种再平衡间隔：`FREQUENCIES = [5, 10, 21, 63]`，分别对应约每周、每 2 周、每月、每季度。

7. 第 1 轮回测——不计交易成本（`fee_model=None`）：
   - 循环跑 4 种再平衡间隔的回测，将结果保存到 `results_no_fee`，以再平衡间隔为键
   - 打印对比表：再平衡间隔、累计收益率、年化波动率、最大回撤、简化夏普、成交笔数

8. 第 2 轮回测——计入交易成本（`fee_model=PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`，本实验具体模拟按成交金额的 0.1% 收取、每笔最低 5 元的佣金，不包括税费和滑点）：
   - 将上述费用模型保存为 `FEE_MODEL`，调用 `run_backtest` 时作为 `fee_model` 传入
   - 循环跑 4 种再平衡间隔的回测，将结果保存到 `results_with_fee`，以再平衡间隔为键，供后续 spec 选取再平衡间隔
   - 打印对比表：再平衡间隔、累计收益率、年化波动率、最大回撤、简化夏普、成交笔数、总手续费
   - 总手续费计算：`sum(float(f.fee) for f in result.trades)`，避免 `Decimal` 格式化问题。手续费显示保留 2 位小数，计算和差值比较使用未舍入值

9. 画净值曲线对比图（`figsize=(12, 6)`，画布大小为 12 英寸×6 英寸）：
   - 4 条曲线分别对应 5、10、21 和 63 个交易日的再平衡间隔，并在图例中标注对应间隔。
   - 4 条曲线均归一化到起点 100。横轴标“年份”，纵轴标“归一化净值（起点=100）”；同时用不同颜色和线型区分曲线。
   - 标题“再平衡间隔对比（计入交易成本）”

10. 打印分析（根据实际数据描述结果方向，不要硬写“更高”或“更低”）：
    - 不计交易成本时，哪个再平衡间隔效果最好？
    - 计入交易成本后，排名有没有变化？
    - 成交笔数和总手续费随再平衡间隔的变化规律
    - “交易不是免费的——每次买卖支付的佣金是实打实的钱。在本次实验中，间隔越短，再平衡越频繁，成交越多，交易成本越高。”
    - “但再平衡间隔的选择不是最关键的问题。更要命的是——2 次再平衡之间如果某只 ETF 暴跌，你只能干等到下一个再平衡日。能不能加一个‘紧急出口’？”

11. 固定窗口参考结果（`START = "2021-01-01"`，`END = "2026-03-18"`），用于判断是否复现书稿：
    - 不计交易成本：5 天 `101.22% / 10.90% / -12.32% / 1.34 / 744`；10 天 `106.80% / 11.19% / -12.44% / 1.36 / 372`；21 天 `95.22% / 11.35% / -14.33% / 1.24 / 177`；63 天 `105.56% / 11.85% / -14.79% / 1.28 / 57`
    - 计入交易成本：5 天 `93.37% / 10.91% / -12.97% / 1.27 / 744 / 4665.12`；10 天 `101.68% / 11.19% / -12.81% / 1.31 / 372 / 3021.42`；21 天 `91.94% / 11.35% / -14.50% / 1.21 / 177 / 2052.37`；63 天 `104.09% / 11.86% / -14.85% / 1.27 / 57 / 925.54`

### 结果呈现

1. 输出不计交易成本的对比表，共 4 行、6 列。
2. 输出计入交易成本的对比表，共 4 行、7 列，并增加“总手续费”列。
3. 绘制计入交易成本时的净值曲线对比图。
4. 根据实际数据生成分析文字，不预设结果方向。

## 验收标准

执行成功的标志：
- 新增的单元格无报错运行完毕
- 不计交易成本和计入交易成本的对比表各有 4 行数据
- 计入交易成本的对比表多一列总手续费。在本次结果中，再平衡间隔越短，成交笔数和总手续费越高
- 净值曲线图显示 4 条线
- 参考结果与上面的固定窗口数值一致，或差异小到只来自格式化四舍五入
