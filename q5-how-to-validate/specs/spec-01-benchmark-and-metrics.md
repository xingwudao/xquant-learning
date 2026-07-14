# Spec: 跟什么比？——基准与风险调整指标

> 在 notebook 当前内核中运行；使用 open-xquant SDK 模块，不使用 `today`、`now()` 或默认截止日期。

## 上下文

本章评估策略的有效性。Q3-Q4 产出了多个策略变体，回测指标看起来不错。但"不错"是跟什么比？年化 15% 好不好，取决于同期市场涨了多少。

本章用四个策略作为"被检查对象"：EqualWeight（Q3 等权）、RiskParity（Q3 风险平价）、TopNRanking（Q3 动量排名）、RiskParity + 5% 止损（Q4 最终产出）。

## 任务

在 notebook `q5-how-to-validate.ipynb` 中创建代码，把策略和买入持有基准放在一起比较，并引入多种风险调整指标。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解 `RunResult` 的评估接口：
   - `result.total_return()` — 累计收益率
   - `result.annualized_return()` — 年化收益率
   - `result.annualized_volatility()` — 年化波动率
   - `result.max_drawdown()` — 最大回撤
   - `result.sharpe_ratio()` — 夏普比（年化收益 / 波动率）
   - `result.calmar_ratio()` — 卡玛比（年化收益 / 最大回撤）
   - `result.sortino_ratio()` — 索提诺比（年化收益 / 下行波动率）

3. 创建 notebook `q5-how-to-validate.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility, Momentum, Ratio`
   - `from oxq.portfolio.optimizers import EqualWeightOptimizer, RiskParityOptimizer, TopNRankingOptimizer`
   - `from oxq.signals import Threshold`
   - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - pandas, numpy, matplotlib.pyplot, Decimal
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 复用 Q3/Q4 的数据和策略配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深300ETF", "513100.SS": "纳指100ETF", "518880.SS": "黄金ETF"}`
   - 数据窗口固定为 `START = "2021-01-01"`、`END = "2026-03-18"`
   - 不要使用 `today`、`pd.Timestamp.now()` 或省略 `end` 的下载方式
   - yfinance 的 `end` 是排他边界，下载时使用 `DOWNLOAD_END = "2026-03-19"`，回测和读取本地数据仍使用 `END`
   - 使用 `YFinanceDownloader` 下载数据，读取时用 `market.get_bars(symbol, START, END)`
   - 构建 `StaticUniverse`
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`
   - 为复现书中原实验语义，使用兼容 broker。手续费仍计入绩效，但不因为手续费现金余量拒绝调仓买单：
     ```python
     class BookCompatibleSimBroker(SimBroker):
         def set_available_cash(self, cash):
             self._available_cash = None
     ```

5. 先阅读 `oxq.portfolio.optimizers` 模块源码，了解 `EqualWeightOptimizer`、`RiskParityOptimizer`、`TopNRankingOptimizer` 的构造参数和 `required_indicators` 属性。

6. 定义四个 portfolio 配置常量：
   - `EW_PORTFOLIO = EqualWeightOptimizer()`
   - `RP_PORTFOLIO = RiskParityOptimizer(volatility_col="vol")`
   - `TNR_PORTFOLIO = TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
   - `RP_SL_PORTFOLIO = RiskParityOptimizer(volatility_col="vol")`（与 RP 相同，止损在运行时指定）

7. 定义辅助函数 `run_strategy(portfolio, indicators=None, freq=10, stop_loss=None)`：
   - `portfolio` 是一个 optimizer 实例（如 `EqualWeightOptimizer()`）
   - `indicators` 是指标字典 `{"列名": (Indicator(), {"参数": 值})}`，例如 `{"vol": (RollingVolatility(), {"column": "close", "period": 20})}`。`indicators=None` 表示无需指标（EqualWeight）
   - 使用 `Threshold` 作为始终为真的信号
   - 规则通过 `Engine.run(rules=[RebalanceFrequencyRule(interval_days=freq), ...])` 传入
   - 组装 Strategy，含交易成本，broker 使用 `BookCompatibleSimBroker(fee_model=FEE_MODEL)`
   - `Engine().run(..., start=START, end=END, rules=rules)`
   - 返回 RunResult
   - 供后续 spec 复用

8. 运行四个策略：
   - EqualWeight：`run_strategy(EW_PORTFOLIO)`
   - RiskParity：`run_strategy(RP_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20})})`
   - TopNRanking：`run_strategy(TNR_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20}), "mom": (Momentum(), {"column": "close", "period": 20}), "ram": (Ratio(), {"col_a": "mom", "col_b": "vol"})})`
   - RiskParity + 止损：`run_strategy(RP_SL_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20})}, stop_loss=0.05)`

9. 构造买入持有基准——等权买入 3 只 ETF，之后不做任何交易：
   - 加载价格数据，每只 ETF 归一化到 1，等权平均
   - 计算基准的累计收益、年化收益、年化波动率、最大回撤、夏普比

10. 打印策略 vs 基准对比表：
   - 列：策略名、累计收益、年化收益、波动率、最大回撤、夏普比、卡玛比、索提诺比
   - 最后一行是等权买入持有基准
   - 额外打印超额收益 / Alpha（策略累计 - 基准累计），并呼应 Q0 提到的 Alpha 概念：「还记得 Q0 说的吗？Beta 是跟着市场赚的钱，Alpha 是比市场多赚的钱——你的技能回报。」

11. 画净值曲线对比图（figsize 12x6）：
   - 4 条策略线（不同颜色实线）+ 1 条基准线（灰色虚线）
   - 归一化到起点 = 100
   - 标题「策略 vs 买入持有基准」
   - 图例放在左上角

12. 打印分析（根据实际数据动态描述方向，不要硬写"更高"或"更低"）：
    - 哪些策略跑赢了基准？哪些没有？
    - 超额收益（Alpha）最大的是哪个？但卡玛比和索提诺比的排名呢？
    - 「年化 15% 好不好？取决于同期等权买入持有赚了多少。跑赢基准的部分，才是你的'本事'——多出来的叫超额收益，也就是 Q0 说的 Alpha。」
    - 「夏普比、卡玛比、索提诺比是三把不同的尺子。夏普比看总波动，卡玛比看最大回撤，索提诺比只看下行波动。你最怕什么风险，就用什么尺子。」
    - 「整体指标看着还行——但这是好几年平均出来的。每一年都赚钱吗？」

## 结果呈现

1. 策略 vs 基准指标对比表（5 行 × 8 列）
2. 超额收益表
3. 净值曲线对比图
4. 分析文字

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 对比表有 5 行（4 策略 + 1 基准），8 个指标列（使用中文指标名：夏普比、卡玛比、索提诺比）
- 净值曲线图显示 5 条线（4 实线 + 1 虚线）
- 超额收益有正有负或全正
- 固定窗口参考结果应接近：
  - EqualWeight 累计收益 `83.59%`
  - RiskParity 累计收益 `101.68%`
  - TopNRanking 累计收益 `131.32%`
  - RP+止损5% 累计收益 `100.79%`
  - 等权买入持有基准累计收益 `92.04%`
