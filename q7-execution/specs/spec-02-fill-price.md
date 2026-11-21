# spec：成交价和交易成本会怎样影响回测结果？——成交价与交易成本测试

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

在 `q7-execution.ipynb` 中已有：
- 目标权重转具体订单的结果，以及 A 股与美股的取整偏差对比

以沪深 300 ETF 为例，假设订单计算时使用的收盘价为 4.27 元。实际下单时价格可能已经变化，需要检查成交价假设和交易成本对结果的影响。

## 任务目标

用本书配套代码所使用的 open-xquant 版本支持的 7 种 `FillPriceMode` 成交价模式做压力测试，再用交易成本分层实验观察费用对结果的影响。

本实验中的“次日”均指下一交易日；`CLOSE` 为当日收盘价模式。本实验将同一交易日的开盘价与收盘价相加后除以 2，所得平均值简称“开收均价”：`MID` 为当日开收均价模式，`NEXT_MID` 为次日开收均价模式。对比表和图例使用上述中文名称。

## 执行要求

1. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.trade.sim_broker` – `SimBroker` 和 `FillPriceMode` 枚举
     - 当前实验使用：`CLOSE`、`MID`、`NEXT_OPEN`、`NEXT_CLOSE`、`NEXT_MID`、`NEXT_AVG`、`NEXT_HL2`
     - 该版本不允许在因果市价单回测中，将沪深 300 ETF、纳指 100 ETF 和黄金 ETF 各自在下一交易日的日内最高价或最低价作为相应订单的模拟成交价。不要在实验中调用对应枚举
     - `NEXT_*` 模式必须显式传入交易日历：`SimBroker(..., fill_price_mode=..., market_calendar=CN_MARKET_CALENDAR)`
   - `oxq.trade.fees` – `PercentageFee(rate, min_fee)`
   - `oxq.trade.slippage` – `PercentageSlippage(rate)`
   - `oxq.core.Engine` – `Engine().run(strategy, market=..., broker=..., start=..., end=...)`
   - `oxq.data` – `YFinanceDownloader`, `LocalMarketDataProvider`
   - 策略相关：`make_strategy` 辅助函数、`Threshold`（信号）、`RiskParityOptimizer`（组合优化器）、`RebalanceFrequencyRule`、`StopLossRule`
     - `from oxq.signals import Threshold`
     - `from oxq.portfolio.optimizers import RiskParityOptimizer`
     - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`

2. 下载数据并加载：
   - 投资对象：510300.SS、513100.SS、518880.SS
   - 起始日期：`START = "2021-01-01"`
   - 实验数据截止日期：`END = "2026-03-18"`
   - 下载边界：`DOWNLOAD_END = "2026-03-19"`，用于包含 `2026-03-18` 的历史数据
   - A 股交易日历：`CN_MARKET_CALENDAR = "XSHG"`
   - 用 `YFinanceDownloader` 下载，下载失败时用 try/except 捕获，打印提示并使用本地缓存
   - 用 `LocalMarketDataProvider` 加载

3. 构造策略和交易规则：采用简化风险平价权重分配方法，并使用第 4 章介绍的再平衡交易规则和止损交易规则。将再平衡间隔固定为 21 个交易日、止损阈值固定为 10%；这不是第 4 章中按简化夏普选出的配置。
   - 用 `make_strategy(name)` 辅助函数构造策略：创建 `Threshold` 信号，配置 `required_indicators`（`RollingVolatility`），使用 `RiskParityOptimizer(volatility_col="vol")` 作为简化风险平价组合优化器
   - 用 `make_rules()` 辅助函数构造规则：`[RebalanceFrequencyRule(interval_days=21), StopLossRule(threshold=0.10)]`
   - 所有 `Engine.run()` 调用需传入 `rules=make_rules()` 参数

4. 本书所用 open-xquant 版本的成交价模式压力测试：
   - 场内 ETF 佣金模型：`PercentageFee(rate=Decimal("0.0001"), min_fee=Decimal("5"))`。本实验的 3 只场内 ETF 不涉及证券交易印花税；每笔成交佣金最低 5 元是实验设定，不代表所有券商都采用相同规则
   - 显式定义 `FILL_PRICE_MODES = (CLOSE, MID, NEXT_OPEN, NEXT_CLOSE, NEXT_MID, NEXT_AVG, NEXT_HL2)`，不要遍历完整 `FillPriceMode` 枚举
   - 对上述模式分别创建 `SimBroker`，跑完整回测
   - 对所有 `NEXT_*` 模式传入 `market_calendar=CN_MARKET_CALENDAR`
   - 打印对比表：成交价模式、累计收益率、年化收益率、最大回撤、简化夏普、成交笔数

5. 画净值曲线图（画布大小为 12 英寸×8 英寸，上下 2 个子图，高度比 3:1）：
   - 上图绘制 `CLOSE`、`MID`、`NEXT_OPEN`、`NEXT_CLOSE`、`NEXT_MID`、`NEXT_AVG` 和 `NEXT_HL2` 这 7 种成交价模式的净值曲线，各曲线均归一化到起点 100。`CLOSE`、`MID`、`NEXT_OPEN`、`NEXT_CLOSE`、`NEXT_MID`、`NEXT_AVG` 和 `NEXT_HL2` 依次使用绿色实线、灰色点划线、蓝色实线、橙色虚线、紫色虚线、红色点线和青绿色点线。图例标注 7 种模式的名称。
   - 下图绘制除 `CLOSE` 外其余 6 种模式相对 `CLOSE` 的归一化净值差，各条差值曲线沿用上图对应模式的颜色和线型。上图纵轴标“归一化净值（起点=100）”，下图纵轴标“归一化净值差”，共享横轴标“年份”。
   - 对每个交易日，取所有次日成交价模式相对 `CLOSE` 的最小差值和最大差值，再用 `fill_between` 填充两者之间的区域，并以浅橙色显示。在下图图例中标注“次日成交价模式的净值差区间”，不要将这项图例放到上图。
   - 在图题前的图注中说明：“下图中各条曲线的数值，均为相应成交价模式的归一化净值减去当日收盘价模式的归一化净值。”下图纵轴只标“归一化净值差”，不再使用“各模式 − 当日收盘价模式”这样的省略表达。
   - 用 `layout='constrained'` 而非 `plt.tight_layout()`
   - 打印分析：当日收盘价模式的累计收益率、各次日成交价模式相对当日收盘价模式的累计收益率差，以及次日成交价模式中最高累计收益率与最低累计收益率之间的差距

6. 3 组交易成本条件对比（次日开盘价模式）：
   - 第 1 组：不计交易成本 – `SimBroker(fill_price_mode=FillPriceMode.NEXT_OPEN, market_calendar=CN_MARKET_CALENDAR)`
   - 第 2 组：计入佣金 – `PercentageFee(rate=Decimal("0.0001"), min_fee=Decimal("5"))`（佣金费率为万分之一，即 0.01%）
   - 第 3 组：计入佣金和滑点 – 上述佣金 + `PercentageSlippage(rate=Decimal("0.001"))`，滑点率设为千分之一（0.1%）。以次日开盘价为基础，买入时上调 0.1%，卖出时下调 0.1%，以模拟滑点
   - 3 组都使用 `FillPriceMode.NEXT_OPEN`，并传入 `market_calendar=CN_MARKET_CALENDAR`
   - 打印对比表：交易成本条件、累计收益率、年化收益率、简化夏普
   - 打印说明：本实验交易的场内 ETF 不涉及证券交易印花税；实际佣金和滑点取决于券商收费标准与市场成交条件

7. 画交易成本分层图（画布大小为 12 英寸×8 英寸，上下 2 个子图，高度比 3:1）：
   - 先将 3 条权益曲线归一化到起点=100（`equity / equity.iloc[0] * 100`），对齐到公共交易日
   - 上图绘制“不计交易成本”组、“计入佣金”组和“计入佣金和滑点”组的归一化净值曲线，分别采用绿色实线、蓝色虚线和红色点划线，并在图例中标注各组名称。上图纵轴标“归一化净值（起点=100）”，下图纵轴标“归一化净值差”，共享横轴标“年份”，两个子图均显示对应年份的刻度数字。
   - 下图绘制 2 条归一化净值差曲线：分别用“计入佣金”组和“计入佣金和滑点”组的归一化净值减去“不计交易成本”组的归一化净值。由于 3 组条件分别运行完整回测，费用和滑点可能改变成交数量及后续路径；结合实际订单和成交结果解释差值，不预设差值始终为负
   - 下图纵轴只标“归一化净值差”，将上述作差方法写入图题前的图注。
   - 用 `layout='constrained'`
   - 打印相邻 2 组累计收益率的差异，以及首尾 2 组的合计差异，明确每次比较的组名、指标和高低方向，并说明差值按未四舍五入的结果计算；不要把独立回测的相邻差值直接当作同一成交路径上的严格费用归因
   - 过渡：以上都是按设定的成交价、佣金和滑点条件作出的“估算”。接入外部模拟交易接口后，还要怎样拆开数据源、订单状态和成交差异？

## 验收标准

执行成功的标志：
- 单元格无报错运行完毕
- 本书所用 open-xquant 版本的成交价模式对比表有 7 行，包含累计收益率和简化夏普
- 净值曲线图展示 7 条线及次日成交价模式的净值差区间填充
- 交易成本对比表有 3 行，分别对应“不计交易成本”组、“计入佣金”组和“计入佣金和滑点”组
- 显示交易成本分层图，图中包含 3 条归一化净值曲线和 2 条归一化净值差曲线，结论与实际订单、成交路径及指标一致
