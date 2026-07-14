# Spec: 能不能找到最赚钱的参数？——参数优化与样本内/样本外

> 所有命令在沙箱外运行。

## 上下文

本章探讨参数优化和过拟合。Q5 的参数敏感性分析使用了默认参数（动量窗口 20、波动率窗口 20、调仓频率 10），看到了 plateau vs peak 的差异。但学员还没有尝试过"从一堆参数中找出最好的"。

承接 Q5 的叙事：TopNRanking 在 2021 年默认参数亏损，在 2017-2020 这段较顺的市场上表现不错。如果我们在较顺的市场上优化参数，找到"最赚钱"的组合，未来遇到不同市场会怎么样？

本实验固定数据截止，保证任意时间重跑都得到同一组切分：
- `DATA_START = "2017-01-01"`
- `ANALYSIS_END = "2026-05-06"`
- `DOWNLOAD_END = "2026-05-07"`（yfinance 的 `end` 为排他边界）
- `IS_START = "2017-01-01"`，`IS_END = "2020-12-31"`
- `OOS_START = "2021-01-01"`，`OOS_END = "2023-01-31"`

## 任务

在 notebook `q6-avoid-overfitting.ipynb` 中用 open-xquant SDK 实现参数网格搜索，并用样本内/样本外方法检验过拟合。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 SDK 模块源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.ParameterSet` — 参数空间定义（`add()`, `add_constraint()`, `grid()`）
   - `oxq.optimize.GridSearch` — 网格搜索器（`run()` → `SearchResult`）
   - `SearchResult` 的接口：`best`, `top_n()`, `to_dataframe()`
   - `TrialResult` 的属性：`params`, `metric_value`, `run_result`
   - `oxq.core.Engine.run(..., rules=[...])` — 交易规则必须传给 `run()`

3. 创建或更新 notebook 单元格，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility, Momentum, Ratio`
   - `from oxq.signals import Threshold`
   - `from oxq.portfolio.optimizers import TopNRankingOptimizer`
   - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - `from oxq.optimize import ParameterSet, GridSearch`
   - `from oxq.optimize.search import _apply_params, _apply_rule_params, _extract_metric, TrialResult, SearchResult`
   - pandas, numpy, matplotlib.pyplot, Decimal, warnings
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 固定数据和配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 数据下载使用 `DATA_START` 到 `DOWNLOAD_END`
   - 数据读取和所有分析使用 `DATA_START` 到 `ANALYSIS_END`
   - 不允许使用动态运行日期
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`
   - 使用 `BookCompatibleSimBroker(SimBroker)` 复现实验口径：手续费扣绩效，但不因手续费现金余量拒绝调仓买单

5. 构造基础策略（TopNRanking）：
   - 信号：`Threshold`（always-true 信号）
   - `signal.required_indicators` 包含 RollingVolatility（period=20）、Momentum（period=20）、Ratio（mom/vol）
   - 组合优化器：`TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
   - Strategy 构造时传入 `universe=StaticUniverse(symbols=SYMBOLS, name="global-macro-etf")`
   - 基础规则传入 `Engine.run()`：`[RebalanceFrequencyRule(interval_days=10)]`

6. 数据切割：
   - 找到所有标的的共同交易日
   - 样本内：2017-01-01 ~ 2020-12-31（用来优化参数）
   - 样本外：2021-01-01 ~ 2023-01-31（用来验证）
   - 打印全量数据、样本内、样本外的起止日期和天数

7. 用 `ParameterSet` 定义参数空间：
   - `PERIODS = [10, 15, 20, 25, 30]`
   - `FREQS = [5, 10, 15, 21]`
   - `SL_THRESHOLDS = [0.03, 0.05, 0.07, 0.10, 0.15, 0.20]`
   - 无止损组：mom.period × vol.period × RebalanceFrequencyRule.interval_days
   - 含止损组：同上 + StopLossRule.threshold
   - 约束：`RebalanceFrequencyRule.interval_days <= mom.period`
   - 约束：`RebalanceFrequencyRule.interval_days <= vol.period`
   - 打印约束后的有效组合数：无止损组 70，含止损组 420，总计 490

8. 网格搜索必须让规则参数真正生效：
   - 当前 SDK 的 `GridSearch.run()` 可以接收 `rules`，但会先把规则参数尝试应用到 strategy，导致无效参数警告
   - 编写 `RULE_COMPONENTS` 集合区分策略参数和规则参数
   - 编写 `split_strategy_rule_params(params)`
   - 编写 `apply_params_to_strategy_and_rules(strategy, rules, params)`
   - 编写 `run_with_params(strategy, rules, params, market, broker_factory, start, end)`
   - 编写 `grid_search_with_rules(...)`，逐个组合调用 `run_with_params()`，再用 `_extract_metric()` 生成 `TrialResult` / `SearchResult`
   - `broker_factory = lambda: BookCompatibleSimBroker(fee_model=FEE_MODEL)`
   - 运行输出中不得出现无效参数警告

9. 分别运行：
   - 无止损组：样本内 + 样本外
   - 含止损组：样本内 + 样本外
   - 合并结果后按样本内简化夏普排名

10. 分析与展示：
    - 打印 Top 20 及其样本外表现
    - 打印 Top 20 的样本内/样本外夏普统计（均值、范围）
    - 计算全局样本内/样本外相关系数
    - 计算全部组合的夏普衰减分布（均值、中位数）
    - 计算样本外比样本内差的比例
    - 打印各参数维度的样本外均值和推荐区域

11. 画图并保存：
    - 散点图：样本内夏普 vs 样本外夏普，y=x 对角线，Top 20 红色高亮
    - 柱状图：Top 20 的样本内/样本外夏普对比
    - 保存到 `../book/images/02-is-vs-oos-scatter-and-top20.png`

## 参考输出

固定到 `ANALYSIS_END="2026-05-06"` 后，notebook 应复现以下关键结果：

- 全量共同交易日：2017-01-03 ~ 2026-05-06，共 2261 天
- 样本内：2017-01-03 ~ 2020-12-31，共 972 天
- 样本外：2021-01-04 ~ 2023-01-31，共 501 天
- 有效组合数：490
- Top 20 样本内简化夏普均值 1.31，范围 [1.26, 1.37]
- Top 20 样本外简化夏普均值 -0.59，范围 [-0.65, -0.38]
- Top 20 平均衰减 -1.90，20/20 样本外为负
- 全部组合样本内/样本外相关系数 -0.25
- 样本外比样本内差的比例 100%
- 全部组合衰减均值 -1.01，中位数 -0.99
- 推荐区域打印为：动量窗口 20、波动率窗口 30、再平衡频率 21

## 验证

执行成功的标志：
- 新增或更新的单元格无报错运行完毕
- 不使用动态日期
- 参数空间包含无止损组和含止损组，总组合数 490
- 规则参数能真正作用到 `Engine.run(..., rules=...)`
- 运行输出中没有无效参数警告
- Top 20 表有 20 行，包含样本内夏普和样本外夏普
- 散点图和柱状图已显示并保存到书稿图片目录
