# Spec: 一条路径够可靠吗？——交叉验证

> 所有命令在沙箱外运行。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 参数优化 + 样本内/样本外对比
- Walk-forward 分析（Rolling + Anchored）
- 学员已理解参数稳定性的重要性

当前问题：Walk-forward 只用了一套推进规则。如果换一种切法，结论还一样吗？一次验证和多次验证，可信度差多少？

本实验固定数据截止，保证任意时间重跑都得到相同 5 折切分点：
- `DATA_START = "2017-01-01"`
- `ANALYSIS_END = "2026-05-06"`

## 任务

在 notebook 中新建或更新代码单元格，用当前 open-xquant SDK 的 `TimeSeriesCV.split()` 生成时间序列交叉验证切分，并用本章 helper 在每折训练集上做网格搜索，最后组装为 `CVResult`。

当前 SDK 的 `TimeSeriesCV.cross_validate()` 不接收本章需要的 `rules` 参数；不要直接调用它跑本实验。用本章已有的 `grid_search_with_rules()` 和 `run_with_params()` 保证交易规则参数生效。

## 要求

1. 阅读以下 SDK 模块源码，了解接口的输入、输出和参数含义：
   - `oxq.optimize.TimeSeriesCV`
   - `TimeSeriesCV.split()`
   - `oxq.optimize.CVSplitResult`
   - `oxq.optimize.CVResult`
   - `CVResult.splits`
   - `CVResult.mean_oos_metric()`
   - `CVResult.std_oos_metric()`
   - `CVResult.to_dataframe()`
   - 导入：`from oxq.optimize import TimeSeriesCV, CVSplitResult, CVResult`

2. 复用 Step 2 的参数空间和约束：
   - `wf_paramset`
   - 无止损组 70 组合
   - `strategy_no_sl`
   - `BASE_RULES_NO_SL`

3. TopNRanking 交叉验证：
   - `cv = TimeSeriesCV(n_splits=5, expanding=True)`
   - `n_splits=5`：机器学习教材常用默认值；在本数据范围上每折验证段约 1.6 年，长度足够
   - `expanding=True`：训练集逐折扩大，与 Step 2 的 Anchored 思路一致
   - 数据范围：`start=DATA_START`, `end=ANALYSIS_END`
   - 不允许使用动态日期

4. 编写 `cross_validate_with_rules(cv, strategy, rules, paramset, start, end)`：
   - 遍历 `cv.split(start, end)` 得到每折日期
   - 每折训练集调用 `grid_search_with_rules(...)`
   - 取 `search_result.best.params`
   - 用同一参数在测试段调用 `run_with_params(...)`
   - 用 `CVSplitResult(...)` 记录每折
   - 最后返回 `CVResult(splits=..., metric="sharpe_ratio", metric_direction="maximize")`

5. 分析结果：
   - 用 `cv_result.to_dataframe()` 打印汇总表
   - 用 for 循环逐折打印：训练时段、验证时段、最优参数、样本内夏普、样本外夏普、样本外收益
   - 打印 `mean_oos_metric()` ± `std_oos_metric()`
   - 打印样本外范围 [min, max]
   - 从 `cv_result.splits` 提取每折 `best_params`，统计唯一参数组合数

6. 参数判断：
   - 提取每折的 mom.period / vol.period / interval_days
   - 对每个参数打印完整列表、最常出现值和出现次数
   - 动量窗口 20 在 3/5 折出现，标注为多数折一致
   - 波动率窗口范围 10-30，标注为不稳定
   - 调仓频率 15 在 3/5 折出现，标注为多数折一致
   - 计算变异系数 = `std_oos / abs(mean_oos)`
   - 统计样本外夏普为负的折数

7. 画交叉验证结果图并保存：
   - 图（figsize 12×6）
   - 柱状图：每折的样本内夏普和样本外夏普
   - 画样本外均值水平线
   - 标题「5 折交叉验证：每折的样本内与样本外简化夏普」
   - 保存到 `../book/images/07-cross-validation-5fold.png`

8. 打印分析：
   - 5 折中有几种唯一参数组合
   - 哪些参数区域与 Step 2 Anchored 高频参数一致
   - 样本外夏普的范围和标准差
   - 交叉验证的价值：不是给你"最优参数"，而是告诉你"参数选择有多可靠"
   - 过渡：到这里，我们检验了参数选择的各种方式。但还有一种过拟合更隐蔽——不是参数选错了，而是规则太多了。

## 参考输出

固定到 `ANALYSIS_END="2026-05-06"` 后，notebook 应复现以下关键结果：

- 5 折结果表有 5 行
- Fold 1：train 2017-01-01 ~ 2018-07-22，test 2018-07-23 ~ 2020-02-11，参数 20/30/15，IS 1.34，OOS 1.04，OOS return 25.11%
- Fold 2：train 2017-01-01 ~ 2020-02-11，test 2020-02-12 ~ 2021-09-02，参数 20/15/15，IS 1.61，OOS 1.23，OOS return 41.72%
- Fold 3：train 2017-01-01 ~ 2021-09-02，test 2021-09-03 ~ 2023-03-24，参数 30/10/10，IS 1.09，OOS -0.26，OOS return -6.84%
- Fold 4：train 2017-01-01 ~ 2023-03-24，test 2023-03-25 ~ 2024-10-13，参数 30/10/10，IS 0.88，OOS 0.68，OOS return 13.62%
- Fold 5：train 2017-01-01 ~ 2024-10-13，test 2024-10-14 ~ 2026-05-05，参数 20/15/15，IS 0.95，OOS 1.73，OOS return 60.79%
- 样本外简化夏普 0.88 ± 0.74
- 样本外范围 [-0.26, 1.73]
- 唯一参数组合 3/5
- 1/5 折样本外夏普为负
- 变异系数约 0.84

## 验证

执行成功的标志：
- 新增或更新的单元格无报错运行完毕
- 不使用动态日期
- 5 折结果表有 5 行，包含训练/验证时段、最优参数、样本内/样本外夏普
- 汇总包含 `mean_oos_metric()` ± `std_oos_metric()`
- 柱状图显示 5 折的样本内/样本外夏普对比，含均值水平线
- 图已保存到书稿图片目录
