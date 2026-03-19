# Spec: 参数动一动，崩不崩？——参数敏感性

> 所有命令在沙箱外运行。

## 上下文

在 `q5-how-to-validate.ipynb` 中已有：
- 四个策略的整体指标、逐年收益、月度分布、回撤深度分析
- 学员已建立了多维度评估的认知

当前问题：所有分析都基于特定参数（period=20, frequency=10, threshold=0.05）。如果参数稍微变一下，结论还成立吗？

## 任务

在 notebook 中新建代码单元格，扫描关键参数的敏感性，对比不同策略的稳健程度。

## 要求

1. RiskParity 波动率窗口敏感性：
   - 扫描 `vol_period = [10, 15, 20, 25, 30, 40]`
   - 对每组参数构造 `RiskParityOptimizer(volatility_col="vol")` 并调用 `run_strategy(portfolio, indicators=[RollingVolatility(period=vol_period)], freq=10)`
   - 打印对比表（6 行 × 5 列）：窗口、累计收益、夏普比、卡玛比、最大回撤

2. TopNRanking 动量窗口敏感性：
   - 扫描 `mom_period = [10, 15, 20, 25, 30, 40]`（波动率窗口固定 20）
   - 对每组参数构造 `TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)` 并调用 `run_strategy(portfolio, indicators=[...], freq=10)`
   - 打印对比表（6 行 × 5 列）：窗口、累计收益、夏普比、卡玛比、最大回撤

3. 止损阈值敏感性：
   - 标题注明「基于 RiskParity 策略，调仓频率 10 天」
   - 扫描 `thresholds = [0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]` + 无止损
   - 对每组参数调用 `run_strategy(RiskParityOptimizer(volatility_col="vol"), indicators=[...], freq=10, stop_loss=threshold)`
   - 打印对比表（8 行 × 5 列）：止损阈值、累计收益、夏普比、最大回撤、交易次数

4. 计算每组的夏普比极差（最大夏普比 - 最小夏普比），打印对比：
   - RiskParity 夏普比极差
   - TopNRanking 夏普比极差
   - 标注哪个是"高原型"（极差小），哪个是"山峰型"（极差大）

5. 画参数敏感性折线图（figsize 15x5，1x3 子图）：
   - 子图 1：RiskParity vol_period（x 轴）vs 夏普比（y 轴），标题「RiskParity 波动率窗口」
   - 子图 2：TopNRanking mom_period（x 轴）vs 夏普比（y 轴），标题「TopNRanking 动量窗口」
   - 子图 3：止损阈值（x 轴）vs 夏普比（y 轴），无止损用虚线标注，标题「RiskParity 止损阈值」
   - 三个子图的 y 轴范围统一，方便对比波动幅度

6. 打印分析（根据实际数据动态描述方向）：
   - RiskParity 的夏普比极差 vs TopNRanking 的夏普比极差
   - 哪个是"高原型"，哪个是"山峰型"
   - 止损阈值是否存在一个"稳定区间"
   - 「想象你在山上找营地。高原型策略像一片平坦的高原——站在哪里都差不多高。山峰型策略像一座尖峰——只有山尖上最高，稍微偏一步就掉下去。你选哪个？」
   - 「好策略不依赖某个'魔法参数'。如果换一个参数值结果就崩了，说明你可能只是运气好选对了那个值。」

## 结果呈现

1. RiskParity 波动率窗口敏感性表（6 行 × 5 列）
2. TopNRanking 动量窗口敏感性表（6 行 × 5 列）
3. 止损阈值敏感性表（8 行 × 5 列，含交易次数）
4. 夏普比极差对比
5. 参数敏感性折线图（1×3）
6. 分析文字

## 验证

执行成功的标志：
- 三组表各有正确的行列数
- 折线图 3 个子图，y 轴范围一致
- 夏普比极差有明确数值，可判断高原型 vs 山峰型
- RiskParity 极差明显小于 TopNRanking 极差
