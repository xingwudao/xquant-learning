# spec：样本内最优参数，到了样本外还有效吗？——参数优化与样本内外比较

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

TopNRanking 配置当前使用的动量窗口和波动率窗口均为 20 个交易日，再平衡间隔为 10 个交易日。需要检验在 2017 至 2020 年的数据中选出的参数，到了 2021 年 1 月 1 日至 2023 年 1 月 31 日的数据中是否仍有相近表现。

## 任务目标

对参数进行网格搜索，比较样本内表现与样本外表现，识别过拟合风险。

## 执行要求

固定以下日期，保证任意时间重跑都得到同一组切分：`DATA_START = "2017-01-01"`、`ANALYSIS_END = "2026-05-06"`、`DOWNLOAD_END = "2026-05-07"`、`IS_START = "2017-01-01"`、`IS_END = "2020-12-31"`、`OOS_START = "2021-01-01"`、`OOS_END = "2023-01-31"`。yfinance 的 `end` 为排他边界。

1. 获取当前工作目录，以此为根目录操作。

2. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.optimize.ParameterSet` – 参数空间定义（`add()`, `add_constraint()`, `grid()`）
   - `oxq.optimize.GridSearch` – 网格搜索器（`run()` → `SearchResult`）
   - `SearchResult` 的接口：`best`, `top_n()`, `to_dataframe()`
   - `TrialResult` 的属性：`params`, `metric_value`, `run_result`
   - `oxq.core.Engine.run(..., rules=[...])` – 交易规则必须传给 `run()`

3. 创建或更新 Notebook 单元格，导入所需库并设置中文显示：
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
   - 设置 matplotlib 中文显示支持（macOS：Arial Unicode MS、STHeiti；Windows：SimHei；`axes.unicode_minus = True`）

4. 固定数据和配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 数据下载使用 `DATA_START` 到 `DOWNLOAD_END`
   - 数据读取和所有分析使用 `DATA_START` 到 `ANALYSIS_END`
   - 不允许使用动态运行日期
   - `FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`
   - 使用 `BookCompatibleSimBroker(SimBroker)` 复现实验设定：手续费计入绩效，但不会因计入手续费导致可用现金不足而拒绝再平衡买单

5. 构造使用 `TopNRankingOptimizer` 的基础策略：
   - 信号：`Threshold`（always-true 信号）
   - 在 `signal.required_indicators` 中按以下方式注册指标，计算参数放在各指标实例后的字典中：
     ```python
     signal.required_indicators = {
         "vol": (RollingVolatility(), {"column": "close", "period": 20}),
         "mom": (Momentum(), {"column": "close", "period": 20}),
         "ram": (Ratio(), {"col_a": "mom", "col_b": "vol"}),
     }
     ```
   - 组合优化器：`TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
   - Strategy 构造时传入 `universe=StaticUniverse(symbols=SYMBOLS, name="global-macro-etf")`
   - 基础规则传入 `Engine.run()`：`[RebalanceFrequencyRule(interval_days=10)]`

6. 数据切分：
   - 找到所有投资对象的共同交易日
   - 样本内：2017-01-01 至 2020-12-31（用来优化参数）
   - 样本外：2021-01-01 至 2023-01-31（用来验证）
   - 打印全量数据、样本内、样本外的起止日期和共同交易日数量

7. 用 `ParameterSet` 定义参数空间：
   - `PERIODS = [10, 15, 20, 25, 30]`
   - `FREQS = [5, 10, 15, 21]`
   - `SL_THRESHOLDS = [0.03, 0.05, 0.07, 0.10, 0.15, 0.20]`
   - 不采用止损交易规则的组合（简称“无止损组合”）：`mom.period × vol.period × RebalanceFrequencyRule.interval_days`
   - 采用止损交易规则并扫描止损阈值的组合（简称“止损组合”）：在上述参数基础上增加 `StopLossRule.threshold`
   - 约束：`RebalanceFrequencyRule.interval_days <= mom.period`
   - 约束：`RebalanceFrequencyRule.interval_days <= vol.period`
   - 这 2 条是本实验为控制搜索空间而设的研究约束，用来排除再平衡间隔长于任一观察窗口的组合。它们不是普遍适用的金融规则，也不表示再平衡间隔长于观察窗口时信号必然“过期”
   - 打印约束后的有效组合数：无止损组合 70 种，止损组合 420 种，总计 490 种

8. 网格搜索必须让规则参数真正生效：
   - 本书配套代码所使用的 open-xquant 版本中，`GridSearch.run()` 可以接收 `rules`，但会先把规则参数尝试应用到 strategy，导致无效参数警告
   - 编写 `RULE_COMPONENTS` 集合区分策略参数和规则参数
   - 编写 `split_strategy_rule_params(params)`
   - 编写 `apply_params_to_strategy_and_rules(strategy, rules, params)`
   - 编写 `run_with_params(strategy, rules, params, market, broker_factory, start, end)`
   - 各段均从初始资金独立回测，不承接上一段的持仓；指标只使用该段 `start` 至 `end` 的数据计算，不另设早于 `start` 的 `data_start`。段首指标尚未形成时持有现金，待指标形成后再按交易规则买卖。不同窗口参数所需的等待时间可能不同，结果包含这一影响，不代表同一账户连续运行的业绩
   - 编写 `grid_search_with_rules(...)`，逐个组合调用 `run_with_params()`，再用 `_extract_metric()` 生成 `TrialResult` / `SearchResult`
   - `broker_factory = lambda: BookCompatibleSimBroker(fee_model=FEE_MODEL)`
   - 运行输出中不得出现无效参数警告

9. 分别运行：
   - 无止损组合：分别使用样本内数据和样本外数据运行
   - 止损组合：分别使用样本内数据和样本外数据运行
   - 合并结果后按样本内简化夏普排名

10. 分析与展示：
    - 打印按样本内简化夏普排名前 20 的参数组合及其样本外表现
    - 打印这 20 个参数组合的样本内简化夏普与样本外简化夏普统计（均值、范围）
    - 计算全局样本内简化夏普与样本外简化夏普的相关系数
    - 计算全部组合的简化夏普差（样本外简化夏普减去样本内简化夏普）分布，包括均值和中位数
    - 计算样本外简化夏普低于样本内简化夏普的组合比例
    - 打印各参数取值对应的样本外简化夏普均值，仅作事后诊断，不据此重新选择参数或确定推荐区域

11. 画图并保存：
    - 绘制样本内简化夏普与样本外简化夏普的散点图：全部参数组合使用蓝色点，按样本内简化夏普排名前 20 的参数组合使用较大的红色点。另用黑色虚线绘制 *y*=*x* 的数值相等线。
    - 绘制这 20 个参数组合的分组柱状图：每组用蓝色柱表示样本内简化夏普，用红色柱表示样本外简化夏普。
    - 左图标题为“全部 490 种参数组合：样本内简化夏普与样本外简化夏普”，依次分为“全部 490 种参数组合：”“样本内简化夏普与”“样本外简化夏普”3 行。右图标题为“按样本内简化夏普排名前 20 的参数组合”；右图标题与左图中对应红点的图例都分为 2 行，第 1 行为“按样本内简化夏普”，第 2 行为“排名前 20 的参数组合”。
    - 保存到 `../book/images/02-is-vs-oos-scatter-and-top20.png`

## 验收标准

固定到 `ANALYSIS_END="2026-05-06"` 后，Notebook 应复现以下关键结果：

- 全量共同交易日：2017-01-03 至 2026-05-06，共 2261 个
- 样本内：2017-01-03 至 2020-12-31，共 972 个共同交易日
- 样本外：2021-01-04 至 2023-01-31，共 501 个共同交易日
- 有效组合数：490
- 按样本内简化夏普排名前 20 的参数组合，其样本内简化夏普均值为 1.31，范围为 [1.26, 1.37]
- 这 20 个参数组合的样本外简化夏普均值为 −0.59，范围为 [−0.65, −0.38]
- 这 20 个参数组合的平均简化夏普差（样本外简化夏普减去样本内简化夏普）为 −1.90，且样本外简化夏普全部为负
- 全部组合样本内简化夏普与样本外简化夏普的相关系数为 −0.25
- 样本外简化夏普低于样本内简化夏普的组合比例为 100%
- 全部组合简化夏普差的均值为 −1.01、中位数为 −0.99
- 参数分组结果标注为事后诊断，不把样本外简化夏普均值较高的参数区域称为“推荐区域”

### 完成标志

- 新增或更新的单元格无报错运行完毕
- 数据结束日期固定，不随代码运行日期变化
- 参数空间包含无止损组合和止损组合，总组合数为 490
- 规则参数能真正作用到 `Engine.run(..., rules=...)`
- 运行输出中没有无效参数警告
- 参数组合表有 20 行，包含样本内简化夏普与样本外简化夏普
- 散点图和柱状图已显示并保存到书稿图片目录
