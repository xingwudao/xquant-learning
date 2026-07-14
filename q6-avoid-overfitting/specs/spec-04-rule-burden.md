# Spec: 规则越多回测越好——是好事吗？——规则负担

> 所有命令在沙箱外运行。

## 上下文

在 `q6-avoid-overfitting.ipynb` 中已有：
- 参数优化 + 样本内/样本外
- Walk-forward（Rolling + Anchored）
- 交叉验证（5 折 Time-Series Split）

当前问题：前三步都在检验"参数选得对不对"。但还有一种过拟合来自"规则太多"——每加一条规则，就多了一个可以调节的旋钮。旋钮越多，越容易在样本内"调出"好看的结果。

本实验复用 Step 1 的样本内/样本外切分：
- `IS_START = "2017-01-01"`，`IS_END = "2020-12-31"`
- `OOS_START = "2021-01-01"`，`OOS_END = "2023-01-31"`

## 任务

在 notebook 中新建或更新代码单元格，通过两个堆叠实验展示规则负担。

## 要求

1. 阅读以下 SDK 模块源码，了解可用交易规则及其参数：
   - `oxq.rules.RebalanceFrequencyRule` — 调仓频率规则（`interval_days`）
   - `oxq.rules.StopLossRule` — 止损规则（`threshold`）
   - `oxq.rules.TakeProfitRule` — 止盈规则（`threshold`）
   - `oxq.rules.TrailingStopRule` — 移动止损规则（`trail_pct`）
   - `oxq.rules.MaxDrawdownRisk` — 最大回撤风控（`max_drawdown`）
   - `oxq.core.Engine.run(..., rules=[...])`
   - `ParameterSet.add_constraint()` 的约束表达式格式

2. 继续使用 Step 1 的 SDK 兼容 helper：
   - `BookCompatibleSimBroker`
   - `split_strategy_rule_params()`
   - `apply_params_to_strategy_and_rules()`
   - `run_with_params()`
   - `grid_search_with_rules()`
   - 运行输出中不得出现无效参数警告

3. 编写 `run_layer(layer_name, rules, paramset, description)`：
   - 复用 Step 1 的样本内/样本外切分
   - 如果 `paramset` 为空，直接跑固定参数基础策略
   - 如果 `paramset` 非空，只在样本内跑 `grid_search_with_rules(...)`
   - 取样本内最优参数后，只用该最优参数跑一次样本外验证
   - 打印每层组合数、样本内夏普、样本外夏普、收益和衰减

4. **4A 规则堆叠实验**：
   - 基础策略：TopNRankingOptimizer，固定参数 mom=20, vol=20, interval_days=10
   - 规则传入 `Engine().run(..., rules=[...])`
   - Layer 0：基础策略（固定参数，无额外规则）
   - Layer 1：+ 优化调仓频率（interval_days = FREQS，约束 interval_days <= mom.period）
   - Layer 2：+ 优化止损（sl = SL_THRESHOLDS）
   - Layer 3：+ 优化止盈（tp = TP_THRESHOLDS，约束 sl < tp）
   - Layer 4：+ 优化移动止损（trail = TRAIL_PCTS，约束 trail >= sl）
   - Layer 5：+ 最大回撤风控（max_dd = MAX_DD_VALS，约束 max_dd >= sl）
   - 每层在样本内选最优，再到样本外验证
   - 约束过滤不合理组合：止损 < 止盈、移动止损 >= 固定止损、回撤阈值 >= 止损

5. **4B 自由度堆叠实验**：
   - A：只优化动量窗口（1 个自由度，PERIODS）
   - B：+ 波动率窗口（2 个自由度）
   - C：+ 调仓频率（3 个自由度，约束 interval_days <= mom, interval_days <= vol）
   - D：+ 止损阈值（4 个自由度，约束同 C）
   - E：+ 止盈 + 移动止损（6 个自由度，粗网格 [10,20,30]，约束 interval_days<=mom, interval_days<=vol, sl<tp, trail>=sl）
   - 每层在样本内优化所有参数，再到样本外验证
   - 约束过滤不合理组合，与 4A 一致

6. 打印两个汇总表：
   - 4A：层名、描述、组合数、样本内夏普、样本外夏普、衰减、样本内收益、样本外收益
   - 4B：配置名、自由度、组合数、描述、样本内夏普、样本外夏普、衰减

7. 画图并保存：
   - 图（figsize 16×6）
   - 左图：4A 规则堆叠，样本内夏普和样本外夏普随层数变化
   - 右图：4B 自由度堆叠，样本内夏普和样本外夏普随自由度变化
   - 标题分别为「4A 规则堆叠：样本内 vs 样本外」和「4B 自由度越多 ≠ 越好」
   - 保存到 `../book/images/08-rule-burden-4a-4b.png`

8. 打印分析：
   - 4A：找出样本外夏普最高层，并说明后续规则是否成为负担
   - 4B：找出自由度增加但样本外变差的拐点
   - 引用规则负担含义：交易规则本身也可能成为过拟合来源
   - 总结：能用 4 个参数解释的问题，不要急着扩到 6 个

## 参考输出

固定样本内/样本外切分后，notebook 应复现以下关键结果。

4A 规则堆叠：
- Layer 0 基础固定参数：组合 1，IS 0.86，OOS 0.20，衰减 -0.66，IS return 65.24%，OOS return 3.62%
- Layer 1 + 优化调仓频率：组合 3，IS 1.06，OOS -0.14，衰减 -1.20，IS return 91.62%，OOS return -5.41%
- Layer 2 + 优化止损：组合 18，IS 1.25，OOS 0.19，衰减 -1.06，IS return 111.99%，OOS return 3.11%
- Layer 3 + 优化止盈：组合 57，IS 1.56，OOS 0.23，衰减 -1.32，IS return 113.48%，OOS return 4.09%
- Layer 4 + 优化移动止损：组合 183，IS 1.50，OOS -0.36，衰减 -1.86，IS return 80.37%，OOS return -5.73%
- Layer 5 + 最大回撤风控：组合 825，IS 1.50，OOS -0.46，衰减 -1.96，IS return 80.37%，OOS return -6.56%
- Layer 3 是样本外夏普数值最高层，但相对 Layer 0 的提升很小；Layer 4 以后明显有害

4B 自由度堆叠：
- A：1 自由度，5 组合，IS 1.26，OOS -0.65，衰减 -1.91
- B：2 自由度，25 组合，IS 1.35，OOS -0.62，衰减 -1.97
- C：3 自由度，70 组合，IS 1.35，OOS -0.62，衰减 -1.97
- D：4 自由度，420 组合，IS 1.37，OOS -0.55，衰减 -1.92
- E：6 自由度，323 组合，IS 1.64，OOS -0.69，衰减 -2.34
- D 到 E 是自欺欺人的拐点：样本内 +0.27，样本外 -0.15

## 验证

执行成功的标志：
- 新增或更新的单元格无报错运行完毕
- 不使用动态日期
- 4A 汇总表有 6 行（Layer 0-5）
- 4B 汇总表有 5 行（A-E）
- 两张图各显示样本内和样本外两条线
- 图已保存到书稿图片目录
- 运行输出中没有无效参数警告
