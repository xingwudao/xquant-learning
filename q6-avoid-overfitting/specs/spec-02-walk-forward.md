# spec：市场在变，参数也该跟着变吧？——前推验证分析

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 490 种参数组合的网格搜索结果
- 一次样本内简化夏普与样本外简化夏普的对比结果

单次时间切分不能反映参数随市场变化而重新选择时的表现。

## 任务目标

分别采用滚动窗口和锚定窗口进行前推验证，比较 2 种方案在各折中的参数选择和样本外表现。

## 执行要求

沿用 spec 01 的分段独立回测设置：各段从初始资金开始，指标只使用本段数据计算，包含段首等待指标形成的过程，不承接前一段的持仓。

将数据起始日期固定为 `DATA_START = "2017-01-01"`，数据结束日期固定为 `ANALYSIS_END = "2026-05-06"`；数据结束日期不得随代码运行日期变化。复现相同结果还需要使用相同的冻结数据与运行环境。本书配套代码所使用的 open-xquant 版本中，`WalkForward.run()` 不接收本章所需的 `rules` 参数。不得直接调用它运行本实验，应使用本章已有的 `grid_search_with_rules()` 和 `run_with_params()`，以保证交易规则参数生效。

1. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.optimize.WindowResult`
   - `oxq.optimize.WalkForwardResult`
   - `WalkForwardResult.windows`
   - `WalkForwardResult.deterioration()`
   - `WalkForwardResult.to_dataframe()`
   - `WindowResult` 的属性：`train_start`, `train_end`, `test_start`, `test_end`, `best_params`, `in_sample_metric`, `oos_result`
   - 导入：`from oxq.optimize import WindowResult, WalkForwardResult`

2. 复用第 1 个实验中 70 种无止损组合的参数范围和约束：
   - `PERIODS = [10, 15, 20, 25, 30]`
   - `FREQS = [5, 10, 15, 21]`
   - `paramset.add("mom", "period", PERIODS)`
   - `paramset.add("vol", "period", PERIODS)`
   - `paramset.add("RebalanceFrequencyRule", "interval_days", FREQS)`
   - 约束：`RebalanceFrequencyRule.interval_days <= mom.period`
   - 约束：`RebalanceFrequencyRule.interval_days <= vol.period`
   - 约束后 70 种组合

3. 编写窗口辅助函数：
   - `parse_period_offset(period)` 支持 `"2Y"`, `"6M"`, `"126D"` 等表示时间长度的字符串
   - `walk_forward_windows(start, end, train_period, test_period, anchored=False, step=None)`
   - 滚动窗口：训练窗口固定大小并整体向前移动
   - 锚定窗口：训练起点固定为 `DATA_START`，训练窗口逐步扩大
   - 若最后一折验证结束日超过 `ANALYSIS_END`，截断到 `ANALYSIS_END`

4. 编写 `run_walk_forward_with_rules(...)`：
   - 对每个窗口，用训练段调用 `grid_search_with_rules(...)`
   - 取 `search_result.best.params`
   - 用同一参数在验证段调用 `run_with_params(...)`
   - 用 `WindowResult(...)` 记录每折
   - 最后返回 `WalkForwardResult(windows=..., metric="sharpe_ratio", metric_direction="maximize")`

5. 采用滚动窗口进行前推验证：将训练窗口长度设为 `"2Y"`，验证窗口长度设为 `"6M"`，使用 `anchored=False`，使训练窗口保持固定长度并整体向前移动。使用 `start=DATA_START`, `end=ANALYSIS_END`。

6. 采用锚定窗口进行前推验证：将初始训练窗口长度设为 `"2Y"`，验证窗口长度设为 `"6M"`，使用 `anchored=True`，使训练窗口固定起点并逐步扩大。使用 `start=DATA_START`, `end=ANALYSIS_END`。

这里，`train_period="2Y"` 在滚动式前推验证中表示固定的 2 年回看区间，在锚定式前推验证中表示初始训练长度；这项设置不表示 2 年足以覆盖完整市场周期。`test_period="6M"` 表示验证窗口的标准长度为 6 个月：既能观察一段策略表现，也能让当前数据范围内形成多个折。

7. 打印每折详情和汇总：
   - 用 `to_dataframe()` 打印每折：训练时段、验证时段、最优参数、样本内简化夏普与样本外简化夏普
   - 用 `deterioration()` 计算衰减率；本实验保留逐折指标，不调用 `WalkForwardResult.oos_sharpe_ratio()` 计算整体指标，也不拼接各折重新从初始资金开始的净值
   - 从 `windows` 中提取参数列表，统计不同参数组合数
   - 用 `Counter` 找出锚定式中最频繁的参数组合及其出现次数

8. 画前推验证结果图并保存：
   - 在一张大小为 14 英寸×8 英寸的画布中上下排列 2 个子图。
   - 上图绘制滚动式和锚定式每折的样本内简化夏普与样本外简化夏普：滚动式使用红色，锚定式使用蓝色，样本外结果使用实线，样本内结果使用虚线。
   - 下图展示 `mom.period` 和 `interval_days` 的跨折变化：滚动式仍使用红色，锚定式仍使用蓝色，`mom.period` 使用实线，`interval_days` 使用虚线。
   - 上图标题为“每折样本内简化夏普与样本外简化夏普”，纵轴为“简化夏普”；下图标题为“每折样本内选出的参数”，纵轴为“参数值/交易日”。2 个子图的横轴均标为“折次”，刻度使用 1～15，负刻度使用数学减号 `−`
   - 上图图例为“滚动式：样本外简化夏普”“滚动式：样本内简化夏普”“锚定式：样本外简化夏普”“锚定式：样本内简化夏普”；下图图例为“滚动式：动量窗口”“锚定式：动量窗口”“滚动式：再平衡间隔”“锚定式：再平衡间隔”。圆点代表滚动式，方块代表锚定式
   - 成书图片不另设与编号图题重复的总标题；Notebook 独立显示时保留总标题“前推验证分析：滚动式与锚定式”
   - 保存到 `../book/images/04-walk-forward-rolling-vs-anchored.png`

9. 打印分析：
   - 比较锚定式前推验证的参数变化程度和滚动式前推验证的参数变化程度
   - 比较滚动式前推验证的衰减率和锚定式前推验证的衰减率
   - 前推验证的核心价值：不是找“永远最优”的参数，而是检验优化方法在这些历史窗口中是否稳定
   - 过渡：本次前推验证虽然比较了 2 种训练窗口设置，但 2 种方案采用相同的初始训练长度、验证窗口长度和推进步长——如果换一种切分方式，结论还一致吗？

## 验收标准

固定到 `ANALYSIS_END="2026-05-06"` 后，Notebook 应复现以下关键结果：

- 滚动式：15 折，衰减率为 −28.2%，选出的不同参数组合数为 13
- 锚定式：15 折，衰减率为 −15.2%，选出的不同参数组合数为 3
- 前 14 折的验证窗口各为 6 个月，最后 1 折截至 `2026-05-06`，短于 6 个月
- 锚定式最频繁参数组合出现 8/15 折：`mom.period=20`、`vol.period=15`、`RebalanceFrequencyRule.interval_days=15`
- 锚定式参数范围：`mom.period` 为 [20, 30]，`vol.period` 为 [10, 15]，`interval_days` 为 [10, 15]
- 滚动式参数范围：`mom.period` 为 [10, 15, 20, 25, 30]，`vol.period` 为 [10, 15, 25, 30]，`interval_days` 为 [5, 10, 15, 21]

### 完成标志

- 新增或更新的单元格无报错运行完毕
- 数据结束日期固定，不随代码运行日期变化
- 滚动式和锚定式各产出 15 折
- 每折包含训练时段、验证时段、最优参数、样本内简化夏普与样本外简化夏普
- 对比图显示 2 种方案的样本外简化夏普趋势和参数稳定性
- 图已保存到书稿图片目录
- `deterioration()` 返回有效数值
