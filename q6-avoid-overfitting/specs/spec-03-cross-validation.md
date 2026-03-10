# Spec: 一条路径够可靠吗？——交叉验证

> 所有命令在沙箱外运行。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 参数优化 + 样本内/样本外对比
- Walk-forward 分析（Rolling + Anchored）
- 学员已理解参数稳定性的重要性

当前问题：Walk-forward 只用了一种切法。如果换一种切法，结论还一样吗？一次验证和多次验证，可信度差多少？

## 任务

在 notebook 中新建代码单元格，用 `oxq.optimize.TimeSeriesCV` 实现时间序列交叉验证。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.TimeSeriesCV` — 时间序列交叉验证
     - 构造参数：`n_splits`（折数）, `embargo_days`（隔离天数）, `expanding`（扩展/固定窗口）
     - `cross_validate()` → `CVResult`（传入 `paramset` 时自动在每折训练集上做 GridSearch）
     - `split()` → `list[CVSplit]`（仅生成切分，不跑回测）
   - `CVResult` 的接口：
     - `splits` — 每折的 `CVSplitResult` 列表
     - `mean_oos_metric()` — 样本外指标均值
     - `std_oos_metric()` — 样本外指标标准差
     - `to_dataframe()` — 含时段、参数、指标的 DataFrame
   - `CVSplitResult` 的属性：`split`（含 train/test 日期）, `best_params`, `in_sample_metric`, `oos_result`
   - 导入：`from oxq.optimize import TimeSeriesCV`

2. 复用 Step 2 的参数空间和约束（无止损组，70 组合）。

3. TopNRanking 交叉验证：
   - `n_splits=5`, `expanding=True`
   - 数据范围：`DATA_START` 到当前日期
   - 传入 `paramset` 让 `cross_validate()` 自动做每折的 GridSearch

4. 分析结果：
   - 用 `cv_result.to_dataframe()` 打印每折详情
   - `cv_result.mean_oos_metric()` — 样本外夏普均值
   - `cv_result.std_oos_metric()` — 样本外夏普标准差
   - 从 `cv_result.splits` 提取每折的 `best_params`，判断参数一致性

5. 画交叉验证结果图（figsize 12×6）：
   - 柱状图：每折的样本内夏普和样本外夏普
   - 画样本外均值水平线
   - 标题「5 折交叉验证：每折的样本内 vs 样本外夏普比」

6. 打印分析（根据实际数据动态描述）：
   - 5 折中有几折选了相同的参数——参数一致性
   - 样本外夏普的范围和标准差——策略对市场环境的敏感度
   - 交叉验证的价值：不是给你"最优参数"，而是告诉你"参数选择有多可靠"
   - 过渡：到这里，我们检验了参数选择的各种方式。但还有一种过拟合更隐蔽——不是参数选错了，而是规则太多了。

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 5 折结果表有 5 行，包含训练/验证时段、最优参数、样本内/样本外夏普
- 汇总包含 `mean_oos_metric()` ± `std_oos_metric()`
- 柱状图显示 5 折的样本内/样本外夏普对比，含均值水平线
