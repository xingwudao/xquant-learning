# Spec: 市场在变，参数也该跟着变吧？——Walk-Forward 分析

> 所有命令在沙箱外运行。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 490 个参数组合的网格搜索结果
- 样本内/样本外对比，发现严重的过拟合现象
- 学员已理解"把数据切一刀"的验证方法

当前问题：数据只切了一次，只验证了一次。市场在变，2023 年选的参数 2025 年还适用吗？能不能模拟"定期重新优化"的过程？

## 任务

在 notebook 中新建代码单元格，用 `oxq.optimize.WalkForward` 实现 Walk-forward 分析，对比 Rolling 和 Anchored 两种方式。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.WalkForward` — Walk-forward 分析器
     - 构造参数：`paramset`, `train_period`, `test_period`, `step`, `anchored`
     - `train_period` / `test_period` 格式：`"2Y"`, `"6M"`, `"126D"` 等
     - `run()` → `WalkForwardResult`
   - `WalkForwardResult` 的接口：
     - `windows` — 每折的 `WindowResult` 列表
     - `deterioration()` — 返回样本内→样本外衰减比例（负值 = 过拟合）
     - `to_dataframe()` — 含训练/验证时段、参数、指标的 DataFrame
     - `oos_sharpe_ratio()`, `oos_total_return()`, `oos_max_drawdown()`
   - `WindowResult` 的属性：`train_start`, `train_end`, `test_start`, `test_end`, `best_params`, `in_sample_metric`, `oos_result`
   - 导入：`from oxq.optimize import WalkForward`

2. 复用 Step 1 的参数范围和约束（无止损组）：
   - `PERIODS = [10, 15, 20, 25, 30]`
   - `FREQS = [5, 10, 15, 21]`
   - 约束：`RebalanceRule.frequency <= mom.period`，`RebalanceRule.frequency <= vol.period`
   - 约束后 70 组合

3. Rolling Walk-Forward：
   - 训练窗口 `"2Y"`，测试窗口 `"6M"`，`anchored=False`
   - 数据范围：`DATA_START` 到当前日期
   - 用 `rolling_result.to_dataframe()` 查看每折详情
   - 用 `rolling_result.deterioration()` 查看衰减比例

4. Anchored Walk-Forward：
   - 同样参数，`anchored=True`
   - 训练窗口从起点不断扩大

5. 打印每折的详情 + 汇总：
   - 用 `to_dataframe()` 打印每折：训练时段、验证时段、最优参数、样本内/样本外夏普
   - 汇总：`oos_sharpe_ratio()`, `deterioration()`
   - 从 `windows` 中提取参数列表，判断参数稳定性

6. Rolling vs Anchored 对比：
   - 样本外整体夏普：`oos_sharpe_ratio()`
   - 衰减比例：`deterioration()`
   - 参数稳定性（从 `windows` 的 `best_params` 提取对比）

7. 画 Walk-forward 结果图（figsize 14×6）：
   - 上半部分：每折的样本外夏普（Rolling 和 Anchored 各一条线）
   - 下半部分：参数稳定性线图——从 `windows` 的 `best_params` 提取 mom.period 和 frequency，展示每折选择的参数变化趋势
   - 标题「Walk-Forward 分析：Rolling vs Anchored」
   - 注意：monospace 字体区域（如 `family="monospace"` 的文本）只使用 ASCII 字符，不使用中文

8. 打印分析（根据实际数据动态描述）：
   - Anchored 的参数在各折之间是否稳定——参数稳定是好信号
   - Rolling 的参数在各折之间是否变化明显——如果最优参数总在变，怎么知道现在的参数下个月还是最优？
   - `deterioration()` 的量化对比：Rolling 衰减 vs Anchored 衰减
   - Walk-forward 的核心价值：不是找"永远最优"的参数，而是检验优化方法在历史上是否靠谱
   - 过渡：Walk-forward 只用了一种切法——如果数据切的方式不同，结论还一致吗？

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- Rolling 和 Anchored 各产出多折结果（折数取决于数据长度和窗口设置）
- 每折包含训练时段、验证时段、最优参数、样本内/样本外夏普
- 对比图显示两种方式的样本外夏普趋势和参数稳定性
- `deterioration()` 返回有效数值
