# Spec: 能不能找到最赚钱的参数？——参数优化与样本内/样本外

> 所有命令在沙箱外运行。

## 上下文

本章探讨参数优化和过拟合。Q5 的参数敏感性分析使用了默认参数（动量窗口 20、波动率窗口 20、调仓频率 10），看到了 plateau vs peak 的差异。但学员从未尝试过"从一堆参数中找出最好的"——现在要迈出这一步。

承接 Q5 的叙事：TopNRanking 在 2021 年差市场的默认参数，在 2017-2020 好市场上表现不错。如果我们在好市场上优化参数，找到"最赚钱"的组合，未来遇到差市场会怎么样？

## 任务

在 notebook `q6-avoid-overfitting.ipynb` 中创建代码，用 `oxq.optimize` 实现参数网格搜索，并用样本内/样本外方法检验过拟合。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.ParameterSet` — 参数空间定义（`add()`, `add_constraint()`, `grid()`）
   - `oxq.optimize.GridSearch` — 网格搜索器（`run()` → `SearchResult`）
   - `SearchResult` 的接口：`best`, `top_n()`, `to_dataframe()`
   - `TrialResult` 的属性：`params`, `metric_value`, `run_result`

3. 创建 notebook `q6-avoid-overfitting.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility, Momentum, Ratio`
   - `from oxq.signals import Threshold`
   - `from oxq.portfolio.optimizers import TopNRankingOptimizer`
   - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - `from oxq.optimize import ParameterSet, GridSearch`
   - `from oxq.optimize.search import _apply_params, _apply_rule_params`
   - pandas, numpy, matplotlib.pyplot, Decimal
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 复用之前的数据和配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 数据起始日期 `2017-01-01`
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`

5. 构造基础策略（TopNRanking），阅读 `Strategy` 源码了解构造方式：
   - 信号：`Threshold`（always-true 信号），设置 `signal.required_indicators` 包含 RollingVolatility（period=20）、Momentum（period=20）、Ratio（mom/vol）
   - 组合优化器：`TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
   - Strategy 构造：`Strategy(signals={"active": (signal, {"column": "close", "threshold": 0, "relationship": "gt"})}, portfolio=TopNRankingOptimizer(...))`
   - 规则传入 `Engine.run()`：`rules=[RebalanceFrequencyRule(interval_days=10)]`

6. 数据切割——样本内/样本外（时间顺序正确，无前视问题）：
   - 找到所有标的的共同交易日
   - 样本内：2017-01-01 ~ 2020-12-31（好市场，用来优化参数）
   - 样本外：2021-01-01 ~ 2023-01-31（差市场，用来验证）
   - 打印两段的起止日期和天数

7. 用 `ParameterSet` 定义参数空间：
   - 动量和波动率窗口：`PERIODS = [10, 15, 20, 25, 30]`
   - 调仓频率：`FREQS = [5, 10, 15, 21]`
   - 止损阈值：`SL_THRESHOLDS = [0.03, 0.05, 0.07, 0.10, 0.15, 0.20]`
   - 无止损组：mom.period × vol.period × RebalanceFrequencyRule.interval_days
   - 含止损组：同上 + StopLossRule.threshold
   - 约束：调仓频率不应超过信号窗口（`RebalanceFrequencyRule.interval_days <= mom.period`，`RebalanceFrequencyRule.interval_days <= vol.period`）
   - 用 `add_constraint(expr)` 添加约束，格式：`"component.param op component.param"`
   - 打印约束后的有效组合数（用 `len(paramset.grid())`）

8. 网格搜索：
   - `GridSearch.run()` 不支持直接传入 rules，需要编写 `grid_search_with_rules()` 包装函数
   - 包装函数使用 `_apply_params` 和 `_apply_rule_params`（从 `oxq.optimize.search` 导入）将参数应用到 strategy 和 rules 上
   - `broker_factory` 使用 `lambda: SimBroker(fee_model=FEE_MODEL)`
   - 分别对无止损组和含止损组，在样本内和样本外各跑一次
   - 合并结果

9. 分析与展示：
   - 按样本内夏普排名，打印 Top 20 及其样本外表现
   - 打印 Top 20 的样本内/样本外夏普统计（均值、范围）
   - 计算全局样本内/样本外相关系数
   - 计算全部组合的夏普衰减分布（均值、中位数）
   - 计算样本外比样本内差的比例

10. 画两张图：
    - 图 1（figsize 10×8）：样本内夏普 vs 样本外夏普散点图
      - 每个点是一个参数组合
      - 画 y=x 对角线（虚线）——对角线以下说明样本外不如样本内
      - 标注 Top 20（红色大点）
      - 标题「N 个参数组合：样本内 vs 样本外夏普比」
    - 图 2（figsize 12×6）：Top 20 的样本内/样本外夏普对比柱状图
      - 每组两根柱子（样本内 / 样本外）
      - 标题「样本内 Top 20 的"样本外真相"」

11. 打印分析（根据实际数据动态描述）：
    - 样本内 Top 20 的平均夏普，以及样本外的平均夏普
    - 散点图中点集的分布特征（多数在对角线以上还是以下）
    - 总结：参数优化可以帮你找到更好的参数，但如果只看优化时段的结果就做决定，可能只是"记住了"这段数据的特征，而不是发现了真规律。这种现象叫过拟合。
    - 过渡：我们需要更科学的验证方法——只验证一次够吗？市场在变，参数也该跟着变吧？

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 参数空间包含无止损组和含止损组，约束后总组合数约 490
- Top 20 表有 20 行，包含样本内夏普和样本外夏普
- 散点图显示所有组合的样本内 vs 样本外夏普，Top 20 用红色标注
- 柱状图显示 Top 20 的样本内/样本外对比
