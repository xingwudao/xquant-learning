# Spec: 调仓频率——多久调一次才合适？

> 所有命令在沙箱外运行。

## 上下文

本章探讨"什么时候买卖"。Q3 用了三种信号（等权、风险平价、动量排名）。本章选择风险平价（RiskParity）作为基础信号——它始终持有全部 3 只 ETF，方便我们观察止损和止盈规则的效果。Q3 每 10 个交易日调一次仓，但为什么是 10 天？调得更勤或更懒，结果会怎样？

## 任务

在 notebook `q4-when-to-trade.ipynb` 中创建代码，对比不同调仓频率的效果，并首次引入交易成本。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.trade.PercentageFee`
   - `oxq.trade.SimBroker`（重点关注 `fee_model` 参数）
   - `oxq.rules.RebalanceFrequencyRule`
   - `oxq.portfolio.optimizers.RiskParityOptimizer`
   - `oxq.core.Engine`（重点关注 `run(rules=[...])` 参数）、`oxq.core.Strategy`

3. 创建 notebook `q4-when-to-trade.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility`
   - `from oxq.signals import Threshold`
   - `from oxq.portfolio.optimizers import RiskParityOptimizer`
   - `from oxq.rules import RebalanceFrequencyRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - pandas, numpy, matplotlib.pyplot, Decimal
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 复用 Q3 的数据和策略配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深300ETF", "513100.SS": "纳指100ETF", "518880.SS": "黄金ETF"}`
   - 数据起始日期 `START = "2021-01-01"`
   - 数据结束日期 `END = "2026-03-18"`，不要使用 `today` / `now` / SDK 默认最新日期
   - `yfinance` 的 `end` 参数是排他边界，下载时使用 `DOWNLOAD_END = "2026-03-19"`，读取和回测统一使用 `END`
   - 使用 `YFinanceDownloader` 下载数据；下载失败时打印提示并继续使用本地缓存，避免离线复跑失败
   - 构建 `StaticUniverse`，加载数据
   - 计算 `common_trading_days` 交集，后续画图时净值曲线按共同交易日对齐，消除中美节假日差异
   - 定义 `BookCompatibleSimBroker(SimBroker)`：新版 SDK 的 `SimBroker` 会因为 `买入金额 + 手续费` 超过现金而拒单；本书原实验口径是手续费扣绩效，但不让手续费改变调仓成交集合，因此覆盖 `set_available_cash`，在含手续费回测中使用这个兼容 broker
   - 创建 Threshold 信号并绑定所需指标：
     ```python
     signal = Threshold()
     signal.required_indicators = {"vol": (RollingVolatility(), {"column": "close", "period": 20})}
     ```
   - 创建 RiskParityOptimizer：`portfolio = RiskParityOptimizer(volatility_col="vol")`

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

6. 定义 4 种调仓频率：`FREQUENCIES = [5, 10, 21, 63]`，分别对应约每周、两周、每月、每季度。

7. 第一轮回测——不含成本（`fee_model=None`）：
   - 循环跑 4 种频率的回测
   - 打印对比表：频率、累计收益率、年化波动率、最大回撤、夏普比率、交易次数

8. 第二轮回测——含成本（`fee_model=PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`，即千分之一佣金 + 5 元最低）：
   - 循环跑 4 种频率的回测
   - 打印对比表：频率、累计收益率、年化波动率、最大回撤、夏普比率、交易次数、总手续费
   - 总手续费计算：`sum(float(f.fee) for f in result.trades)`，避免 Decimal 格式化问题

9. 画净值曲线对比图（figsize 12x6）：
   - 4 条线对应 4 种频率（含成本版本）
   - 归一化到起点 = 100
   - 标题「调仓频率对比（含交易成本）」

10. 打印分析（根据实际数据动态描述方向，不要硬写"更高"或"更低"）：
    - 不含成本时，哪个频率效果最好？
    - 加上成本后，排名有没有变化？
    - 交易次数和总手续费随频率的变化规律
    - 「每次调仓都不是免费的——佣金和手续费是实打实的钱。频率越高，交易越多，成本越大。」
    - 「但频率的选择不是最关键的问题。更要命的是——两次调仓之间如果某只 ETF 暴跌，你只能干等到下一个调仓日。能不能加一个'紧急出口'？」

11. 固定窗口参考结果（`START = "2021-01-01"`，`END = "2026-03-18"`），用于判断是否复现书稿：
    - 不含成本：5 天 `101.22% / 10.90% / -12.32% / 1.34 / 744`；10 天 `106.80% / 11.19% / -12.44% / 1.36 / 372`；21 天 `95.22% / 11.35% / -14.33% / 1.24 / 177`；63 天 `105.56% / 11.85% / -14.79% / 1.28 / 57`
    - 含成本：5 天 `93.37% / 10.91% / -12.97% / 1.27 / 744 / 4665`；10 天 `101.68% / 11.19% / -12.81% / 1.31 / 372 / 3021`；21 天 `91.94% / 11.35% / -14.50% / 1.21 / 177 / 2052`；63 天 `104.09% / 11.86% / -14.85% / 1.27 / 57 / 926`

## 结果呈现

1. 无成本对比表（4 行，6 列）
2. 含成本对比表（4 行，7 列，多一列"总手续费"）
3. 含成本净值曲线对比图
4. 分析文字

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 无成本和含成本各有 4 行对比数据
- 含成本表多一列总手续费；调仓间隔越短，交易次数和总手续费越高
- 净值曲线图显示 4 条线
- 参考结果与上面的固定窗口数值一致，或差异小到只来自格式化四舍五入
