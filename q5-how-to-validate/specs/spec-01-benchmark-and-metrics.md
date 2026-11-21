# spec：跟什么比？——基准与风险调整指标

> 在 Notebook 当前内核中运行。使用 open-xquant 提供的组件和接口，不使用 `today`、`now()` 或默认截止日期。

## 上下文

当前待评估对象为 EqualWeight、RiskParity、TopNRanking、“RP + 止损 5%”这 4 个配置，其中 RiskParity 和 RP 均指本书采用的简化风险平价配置。现有回测指标缺少统一的比较基准。本实验采用等权买入并持有作为基准，即等权买入 3 只 ETF 后不再调整。后文简称“基准”。

## 任务目标

把 4 个策略配置和基准放在一起比较，并引入多种风险调整指标。

## 执行要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读 open-xquant 回测结果对象 `RunResult` 的源码，了解以下评估接口：
   - `result.total_return()` – 累计收益率
   - `result.annualized_return()` – 年化收益率
   - `result.annualized_volatility()` – 年化波动率
   - `result.max_drawdown()` – 最大回撤
   - `result.sharpe_ratio()` – 简化夏普（每日简单收益率均值/每日简单收益率总体标准差×`√252`，`ddof=0`，无风险收益率设为 0）
   - `result.calmar_ratio()` – 卡玛比（年化收益率/最大回撤的绝对值）
   - `result.sortino_ratio()` – 索提诺比（本书简化实现）：分子为全部每日对数收益率的均值×252，分母为负的每日对数收益率的均方根×`√252`，索提诺比等于分子除以分母；下行判断阈值和无风险收益率均设为 0

3. 创建 Notebook `q5-how-to-validate.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility, Momentum, Ratio`
   - `from oxq.portfolio.optimizers import EqualWeightOptimizer, RiskParityOptimizer, TopNRankingOptimizer`
   - `from oxq.signals import Threshold`
   - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - `pandas`、`numpy`、`matplotlib.pyplot`、`Decimal`
   - 设置 `matplotlib` 中文显示支持（macOS：Arial Unicode MS、STHeiti；Windows：SimHei），并设置 `axes.unicode_minus = True`，使坐标轴负值使用数学减号

4. 复用第 3 章、第 4 章的日线行情数据、标的池和 4 个待评估策略配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深 300 ETF", "513100.SS": "纳指 100 ETF", "518880.SS": "黄金 ETF"}`
   - 数据窗口固定为 `START = "2021-01-01"`、`END = "2026-03-18"`
   - 不要使用 `today`、`pd.Timestamp.now()` 或省略 `end` 的下载方式
   - yfinance 的 `end` 是排他边界，下载时使用 `DOWNLOAD_END = "2026-03-19"`，回测和读取本地数据仍使用 `END`
   - 使用 `YFinanceDownloader` 下载数据，读取时用 `market.get_bars(symbol, START, END)`
   - 构建 `StaticUniverse`
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`
   - 为复现书中原实验语义，使用兼容 broker。手续费仍计入绩效，但不会因计入手续费导致可用现金不足而拒绝再平衡买单：
     ```python
     class BookCompatibleSimBroker(SimBroker):
         def set_available_cash(self, cash):
             self._available_cash = None
     ```

5. 先阅读 `oxq.portfolio.optimizers` 中相关组件的源码，了解 `EqualWeightOptimizer`、`RiskParityOptimizer`、`TopNRankingOptimizer` 的构造参数和 `required_indicators` 属性。

6. 定义 3 个 portfolio 配置常量。“RP + 止损 5%”与 RiskParity 复用同一个 portfolio，止损交易规则在运行时传入：
   - `EW_PORTFOLIO = EqualWeightOptimizer()`
   - `RP_PORTFOLIO = RiskParityOptimizer(volatility_col="vol")`
   - `TNR_PORTFOLIO = TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`

7. 定义辅助函数 `run_strategy(portfolio, indicators=None, freq=10, stop_loss=None)`：
   - `portfolio` 是一个 optimizer 实例（如 `EqualWeightOptimizer()`）
   - `indicators` 是指标字典 `{"列名": (Indicator(), {"参数": 值})}`，例如 `{"vol": (RollingVolatility(), {"column": "close", "period": 20})}`。`indicators=None` 表示无需指标（EqualWeight）
   - 使用 `Threshold` 作为始终为真的信号
   - 规则通过 `Engine.run(rules=[RebalanceFrequencyRule(interval_days=freq), ...])` 传入
   - 组装 `Strategy` 并计入交易成本，broker 使用 `BookCompatibleSimBroker(fee_model=FEE_MODEL)`
   - `Engine().run(..., start=START, end=END, rules=rules)`
   - 返回 RunResult
   - 供后续 spec 复用

8. 运行 4 个策略配置，以各自名称为键，将返回的 `RunResult` 保存到 `results` 字典中，供后续 spec 复用。将 RiskParity 使用的指标字典保存为 `RP_IND`，供后续参数扫描沿用：
   - EqualWeight：`run_strategy(EW_PORTFOLIO)`
   - RiskParity：`run_strategy(RP_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20})})`
   - TopNRanking：`run_strategy(TNR_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20}), "mom": (Momentum(), {"column": "close", "period": 20}), "ram": (Ratio(), {"col_a": "mom", "col_b": "vol"})})`
   - RP + 止损 5%：`run_strategy(RP_PORTFOLIO, indicators={"vol": (RollingVolatility(), {"column": "close", "period": 20})}, stop_loss=0.05)`

9. 构造基准——用归一化价格近似表示等权买入 3 只 ETF 后一直持有的路径，之后不做任何调整：
   - 加载价格数据，每只 ETF 归一化到 1，等权平均
   - 不扣初始买入费用，也不模拟整手交易，这些设置与 4 个策略配置采用的设置并不完全相同。这是一项便于比较的简化基准
   - 计算基准的累计收益率、年化收益率、年化波动率、最大回撤、简化夏普。年化收益率按相邻净值之间的收益间隔数换算，年化波动率用每日对数收益率，简化夏普用每日简单收益率且总体标准差取 `ddof=0`，均按 252 个交易日年化

10. 打印策略与基准对比表：
   - 列：策略配置名、累计收益率、年化收益率、年化波动率、最大回撤、简化夏普、卡玛比、索提诺比
   - 最后一行是等权买入并持有基准
   - 额外打印相对基准的累计收益率差（策略累计收益率−基准累计收益率），差值换算为百分点，并统一使用“相对基准的累计收益率差”这一名称

11. 画净值曲线对比图（画布大小为 12 英寸×6 英寸）：
   - EqualWeight、RiskParity、TopNRanking 和“RP + 止损 5%”的净值曲线分别使用蓝色实线、橙色虚线、绿色点划线和黄色点线，色号依次为 `#4472C4`、`#ED7D31`、`#70AD47` 和 `#FFC000`。等权买入并持有基准使用灰色 `#A5A5A5` 虚线。
   - 归一化到起点=100。横轴标“年份”，纵轴标“归一化净值（起点=100）”；图例中的基准写为“等权买入并持有”
   - 标题“策略配置与等权买入并持有基准对比”
   - 图例放在左上角

12. 打印分析（根据实际数据描述结果方向，不要硬写“更高”或“更低”）：
    - 哪些策略跑赢了基准？哪些没有？
    - 相对基准的累计收益率差最大的是哪个？但卡玛比和索提诺比的排名呢？
    - “年化收益率为 15% 好不好？取决于同期基准赚了多少。先看策略的累计收益率相对基准高出或低了多少个百分点，再结合风险指标判断代价。”
    - “简化夏普、卡玛比、索提诺比可以看作 3 把不同的尺子。简化夏普看总波动，卡玛比看最大回撤，索提诺比只看下行风险。你最怕什么风险，就优先看对应的尺子。”
    - 说明等权配置和基准不依赖滚动指标，其他 3 个策略配置需要等待相应指标形成有效值。本次比较不表示各配置在完全相同的日期开始持仓。
    - “整体指标看着还行——但这反映的是好几年的整体表现。每一年都赚钱吗？”

## 验收标准

1. 输出策略配置与基准指标对比表，共 5 行、8 列。
   - 基准行的卡玛比和索提诺比填“—”，表示本实验未计算这 2 个结果，不表示数值为 0
2. 输出相对基准的累计收益率差表，单位为百分点。
3. 绘制净值曲线对比图。
4. 根据实际数据生成分析文字，不预设结果方向。

执行成功的标志：
- 新增的单元格无报错运行完毕
- 对比表有 5 行（4 个策略配置和 1 个基准）、8 列（策略配置名和 7 项指标，使用中文指标名：简化夏普、卡玛比、索提诺比）
- 净值曲线图显示 5 条线，颜色、线型及图例与执行要求一致
- 相对基准的累计收益率差按实际结果报告，单位为百分点，不预设正负方向
- 固定窗口参考结果应接近：
  - EqualWeight 累计收益率 `83.59%`
  - RiskParity 累计收益率 `101.68%`
  - TopNRanking 累计收益率 `131.32%`
  - RP + 止损 5% 累计收益率 `100.79%`
  - 等权买入并持有基准累计收益率 `92.04%`
