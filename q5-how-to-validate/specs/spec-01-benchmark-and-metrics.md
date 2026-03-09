# Spec: 跟什么比？——基准与风险调整指标

> 所有命令在沙箱外运行。

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
   - `from oxq.signals import EqualWeight, RiskParity, TopNRanking`
   - `from oxq.rules import RebalanceRule, StopLossRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - pandas, numpy, matplotlib.pyplot, Decimal
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 复用 Q3/Q4 的数据和策略配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深300ETF", "513100.SS": "纳指100ETF", "518880.SS": "黄金ETF"}`
   - 数据起始日期 `START = "2021-01-01"`
   - 使用 `YFinanceDownloader` 下载数据
   - 构建 `StaticUniverse`
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`

5. 定义辅助函数 `run_strategy(signal_cfg, indicators_cfg, freq=10, stop_loss=None)`：
   - 组装 Strategy，含交易成本
   - 返回 RunResult
   - 供后续 spec 复用

6. 运行四个策略：
   - EqualWeight：无指标，`(EqualWeight(), {})`
   - RiskParity：`vol` 指标（period=20），`(RiskParity(), {"vol": "vol"})`
   - TopNRanking：`vol`+`mom`+`ram` 指标，`(TopNRanking(), {"score": "ram", "n": 3, "filter_negative": True})`
   - RiskParity + 止损：同 RiskParity，额外 `stop_loss=0.05`

7. 构造买入持有基准——等权买入 3 只 ETF，之后不做任何交易：
   - 加载价格数据，每只 ETF 归一化到 1，等权平均
   - 计算基准的累计收益、年化收益、年化波动率、最大回撤、夏普比

8. 打印策略 vs 基准对比表：
   - 列：策略名、累计收益、年化收益、波动率、最大回撤、夏普比、卡玛比、索提诺比
   - 最后一行是等权买入持有基准
   - 额外打印超额收益 / Alpha（策略累计 - 基准累计），并呼应 Q0 提到的 Alpha 概念：「还记得 Q0 说的吗？Beta 是跟着市场赚的钱，Alpha 是比市场多赚的钱——你的技能回报。」

9. 画净值曲线对比图（figsize 12x6）：
   - 4 条策略线（不同颜色实线）+ 1 条基准线（灰色虚线）
   - 归一化到起点 = 100
   - 标题「策略 vs 买入持有基准」
   - 图例放在左上角

10. 打印分析（根据实际数据动态描述方向，不要硬写"更高"或"更低"）：
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
