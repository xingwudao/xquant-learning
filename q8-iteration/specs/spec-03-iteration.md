# Spec: 怎么改？——假设驱动的对照实验

> 所有命令在沙箱外运行。

## 上下文

在 `q8-iteration.ipynb` 中已有：
- Step 1 的监控仪表盘（恶化时段检测）
- Step 2 的三步诊断（执行 OK、市场状态变了、参数有改进空间）
- 已定义的变量：`result_base`、`equity`、`daily_ret`、`detector`、`high_vol_mask`、`market_vol`、`SYMBOLS`、`NAMES`、`START`、`today`、`market`、`make_strategy`、`make_rules`、`FEE_MODEL`、`BEST_FREQ`、`BEST_SL`

诊断结论：策略对高波动的市场状态没有应对方案。现在用假设驱动的对照实验来迭代改进。

## 任务

在 notebook 中新建代码单元格，完成两轮迭代实验（调仓频率 + 波动率过滤），使用 Strategy 的 `hypothesis`/`objectives` 字段展示完整的实验工作流，最后用 `ExperimentLog` 记录迭代历史。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.core.strategy` — `Strategy` 的 `hypothesis: str` 和 `objectives: dict` 字段
   - `oxq.core.engine` — `Engine.run()` 方法（注意 `rules` 参数）
   - `oxq.portfolio.optimizers` — `RiskParityOptimizer`、`VolFilteredOptimizer`（包装器，高波动期将权重缩放 0.5）
   - `oxq.observe` — `ExperimentLog`（`add()` 方法、`to_dataframe()` 方法）

2. 迭代 1——调仓频率对照实验：
   - 创建 Strategy 时填写 `hypothesis="缩短调仓频率能改善高波动期表现"` 和对应的 `objectives`
   - 打印策略的 hypothesis 和 objectives 字段值
   - 对 6 种频率（5/10/15/21/42/63 天）分别跑回测，`Engine.run()` 传入 `rules=make_rules(freq=频率)`
   - 对每种频率，计算高波动时段的夏普（用 `high_vol_mask` 筛选对应日期的日收益）
   - 打印全时段指标表：频率、年化收益、最大回撤、夏普比率、高波动夏普，21 天行标注"-- 基准"
   - 画净值对比图（figsize 14×7，6 条线，21 天加粗），图例标注"高波动夏普"而非全时段夏普
   - 假设验证：先打印引导（"要看最后一列高波动夏普，不是倒数第二列全时段夏普"），再对比基准和最优频率的高波动夏普，判断假设确认还是推翻
   - 保留 `iter1_results` 变量

3. 迭代 2——波动率过滤对照实验：
   - 创建 Strategy 时填写 hypothesis 和 objectives（目标：回撤改善 ≥ 30%，夏普 ≥ 1.0）
   - 打印策略的 hypothesis 和 objectives 字段值
   - 用 `VolFilteredOptimizer` 包装 `RiskParityOptimizer`：高波动期自动将权重缩放 0.5，无需手动修改信号
   - 市场波动率使用 `detector.market_vol`（复用 Step 2 的 MarketStateDetector）
   - 测试 4 种配置：无过滤（基准 `RiskParityOptimizer`）、阈值 10%、阈值 15%、阈值 20%（后三者使用 `VolFilteredOptimizer`）
   - `Engine.run()` 传入 `rules=make_rules()`
   - 打印指标表：配置、年化收益、最大回撤、夏普比率、回撤改善比例
   - 画净值对比图（figsize 14×7，4 条线）
   - 假设验证：检查最佳配置是否满足两个验证标准，判断假设确认还是推翻
   - 打印 Trade-off 分析：年化收益降低了多少换来了多少回撤改善
   - 保留 `iter2_results`、`best_label`、`best_improve`、`best_freq_hv`、`best_hv_sharpe`、`dd_limit` 变量

4. 迭代记录表：
   - 用 `ExperimentLog(name="Q8 迭代实验")` 创建记录
   - 用 `log.add()` 添加两轮迭代的记录（name、observation、hypothesis、criteria、result、conclusion、notes）
   - 用 `log.to_dataframe().to_string(index=False)` 打印记录表
   - 打印过渡：这张表就是你的迭代 SOP

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 迭代 1：6 种频率指标表完整，净值图已保存，假设验证结论已打印
- 迭代 2：4 种配置指标表完整，净值图已保存，假设验证结论已打印
- 迭代记录表包含 2 行（iter1 rejected + iter2 confirmed）
- Strategy 的 hypothesis 和 objectives 字段值在输出中可见
