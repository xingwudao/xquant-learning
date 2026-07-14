# Spec: 市场在变，参数也该跟着变吧？——Walk-forward 分析

> 所有命令在沙箱外运行。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 490 个参数组合的网格搜索结果
- 样本内/样本外对比，发现严重的过拟合现象
- 学员已理解"把数据切一刀"的验证方法

当前问题：数据只切了一次，只验证了一次。市场在变，2023 年选的参数 2025 年还适用吗？能不能模拟"定期重新优化"的过程？

本实验固定数据截止，保证任意时间重跑都得到相同折数、切分点和结果：
- `DATA_START = "2017-01-01"`
- `ANALYSIS_END = "2026-05-06"`

## 任务

在 notebook 中新建或更新代码单元格，用当前 open-xquant SDK 的 `WindowResult` / `WalkForwardResult` 结果结构和本章 helper 实现带 `rules` 的 Walk-forward 分析，对比 Rolling 和 Anchored 两种方式。

当前 SDK 的 `WalkForward.run()` 不接收本章需要的 `rules` 参数；不要直接调用它跑本实验。用本章已有的 `grid_search_with_rules()` 和 `run_with_params()` 保证交易规则参数生效。

## 要求

1. 阅读以下 SDK 模块源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.WindowResult`
   - `oxq.optimize.WalkForwardResult`
   - `WalkForwardResult.windows`
   - `WalkForwardResult.deterioration()`
   - `WalkForwardResult.to_dataframe()`
   - `WalkForwardResult.oos_sharpe_ratio()`
   - `WindowResult` 的属性：`train_start`, `train_end`, `test_start`, `test_end`, `best_params`, `in_sample_metric`, `oos_result`
   - 导入：`from oxq.optimize import WindowResult, WalkForwardResult`

2. 复用 Step 1 的参数范围和约束（无止损组）：
   - `PERIODS = [10, 15, 20, 25, 30]`
   - `FREQS = [5, 10, 15, 21]`
   - `paramset.add("mom", "period", PERIODS)`
   - `paramset.add("vol", "period", PERIODS)`
   - `paramset.add("RebalanceFrequencyRule", "interval_days", FREQS)`
   - 约束：`RebalanceFrequencyRule.interval_days <= mom.period`
   - 约束：`RebalanceFrequencyRule.interval_days <= vol.period`
   - 约束后 70 组合

3. 编写窗口 helper：
   - `parse_period_offset(period)` 支持 `"2Y"`, `"6M"`, `"126D"` 等 DSL
   - `walk_forward_windows(start, end, train_period, test_period, anchored=False, step=None)`
   - Rolling：训练窗口固定大小，窗口向前滑动
   - Anchored：训练起点固定为 `DATA_START`，训练窗口逐步扩大
   - 若最后一折测试结束日超过 `ANALYSIS_END`，截断到 `ANALYSIS_END`

4. 编写 `run_walk_forward_with_rules(...)`：
   - 对每个窗口，用训练段调用 `grid_search_with_rules(...)`
   - 取 `search_result.best.params`
   - 用同一参数在测试段调用 `run_with_params(...)`
   - 用 `WindowResult(...)` 记录每折
   - 最后返回 `WalkForwardResult(windows=..., metric="sharpe_ratio", metric_direction="maximize")`

5. Rolling Walk-forward：
   - 训练窗口 `"2Y"`：覆盖一个完整中期周期，给参数优化足够样本
   - 测试窗口 `"6M"`：足够长以观察策略表现，又足够短以让多个折落进数据范围
   - `anchored=False`
   - `start=DATA_START`, `end=ANALYSIS_END`

6. Anchored Walk-forward：
   - 同样训练窗口 `"2Y"` 和测试窗口 `"6M"`
   - `anchored=True`
   - `start=DATA_START`, `end=ANALYSIS_END`

7. 打印每折详情和汇总：
   - 用 `to_dataframe()` 打印每折：训练时段、验证时段、最优参数、样本内/样本外夏普
   - 汇总：`oos_sharpe_ratio()`、`deterioration()`
   - 从 `windows` 中提取参数列表，统计唯一参数组合数
   - 用 `Counter` 找 Anchored 中最频繁参数组合和出现次数

8. 画 Walk-forward 结果图并保存：
   - 图（figsize 14×8）
   - 上半部分：每折样本外夏普（Rolling 和 Anchored 各一条线）
   - 下半部分：参数稳定性线图，展示 mom.period 和 interval_days 的跨折变化
   - 标题「前推验证分析：滚动式与锚定式」
   - 保存到 `../book/images/04-walk-forward-rolling-vs-anchored.png`

9. 打印分析：
   - Anchored 的参数是否稳定
   - Rolling 的参数是否变化明显
   - Rolling 和 Anchored 的衰减对比
   - Walk-forward 的核心价值：不是找"永远最优"的参数，而是检验优化方法在历史上是否靠谱
   - 过渡：Walk-forward 只用了一种推进规则——如果数据切的方式不同，结论还一致吗？

## 参考输出

固定到 `ANALYSIS_END="2026-05-06"` 后，notebook 应复现以下关键结果：

- Rolling：15 折
- Rolling 样本外整体简化夏普 0.11
- Rolling 衰减 -28.2%
- Rolling 唯一参数组合 13/15
- Anchored：15 折
- Anchored 样本外整体简化夏普 0.14
- Anchored 衰减 -15.2%
- Anchored 唯一参数组合 3/15
- Anchored 最频繁参数组合出现 8/15 折：mom.period=20、vol.period=15、RebalanceFrequencyRule.interval_days=15
- Anchored 参数范围：mom [20, 30]，vol [10, 15]，interval_days [10, 15]
- Rolling 参数范围：mom [10, 15, 20, 25, 30]，vol [10, 15, 25, 30]，interval_days [5, 10, 15, 21]

## 验证

执行成功的标志：
- 新增或更新的单元格无报错运行完毕
- 不使用动态日期
- Rolling 和 Anchored 各产出 15 折
- 每折包含训练时段、验证时段、最优参数、样本内/样本外夏普
- 对比图显示两种方式的样本外夏普趋势和参数稳定性
- 图已保存到书稿图片目录
- `deterioration()` 返回有效数值
