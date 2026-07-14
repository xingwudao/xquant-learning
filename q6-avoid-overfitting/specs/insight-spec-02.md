# Insight: spec-02-walk-forward — Rolling vs Anchored Walk-forward 分析

> 迁移复盘：2026-07-11 已按固定实验截止日更新。
> 本文档定位：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标。

---

## 一、迁移结论

本 spec 已从早期动态结束日写法迁移为固定窗口：

- `DATA_START = "2017-01-01"`
- `ANALYSIS_END = "2026-05-06"`
- 训练窗口 `"2Y"`
- 测试窗口 `"6M"`
- Rolling 和 Anchored 均固定为 15 折

迁移后，notebook 不再依赖运行当天日期，折数、切分点和最终图表可以稳定复现。

当前 SDK 的公开 Walk-forward 运行器不接收本章实验所需的 `rules` 参数。Notebook 因此保留 `WindowResult` / `WalkForwardResult` 结果结构，但用本章 helper 逐窗口执行：

- 训练段：`grid_search_with_rules(...)`
- 测试段：`run_with_params(...)`
- 每折结果：`WindowResult(...)`
- 汇总结果：`WalkForwardResult(...)`

这不是改变实验含义，而是让交易规则参数在当前 SDK 中真正生效。

---

## 二、与 notebook 的同步点

已经同步的关键点：

- 参数空间统一使用 `RebalanceFrequencyRule.interval_days`
- 无止损参数空间固定为 70 组合
- Rolling 使用固定长度训练窗口
- Anchored 固定训练起点并逐步扩展训练集
- 图像保存到 `../book/images/04-walk-forward-rolling-vs-anchored.png`
- 输出分析包含参数稳定性、唯一参数组合数、衰减对比和 Anchored 高频参数

迁移后的参考结果：

- Rolling 样本外整体简化夏普 0.11
- Rolling 衰减 -28.2%
- Rolling 唯一参数组合 13/15
- Anchored 样本外整体简化夏普 0.14
- Anchored 衰减 -15.2%
- Anchored 唯一参数组合 3/15
- Anchored 高频组合 8/15：mom.period=20、vol.period=15、interval_days=15

---

## 三、最佳实践

本 spec 现在示范了循环型实验的三个关键要求。

第一，循环边界必须全锁死。起始日、结束日、训练窗口、测试窗口、步长共同决定折数和切分点，任何一个漂移都会改变结果。

第二，复用前一步参数空间时必须复用命名。跨 spec 的组件名和参数名不能漂移，否则约束和调参会作用到错误对象，甚至静默失效。

第三，SDK 结果结构和执行 helper 可以分离。当前 SDK 暂未直接支持本实验所需的带规则 Walk-forward 运行，但仍可以复用结果对象，让 notebook 输出、图表和后续分析保持标准形态。

---

## 四、可沉淀的方法点

- 对照实验型 spec 适合讲 Rolling vs Anchored：读者能直接比较“只看最近数据”和“逐步累积历史数据”的取舍。
- 循环结构 spec 必须考虑乘法成本：70 组合 × 15 折 × 2 种切法，已经足够重，不应在本步骤继续加入止损维度。
- 参数稳定性要契约化：不仅打印每折收益，还要打印参数集合、唯一组合数和高频参数。
- 当 SDK 版本变化导致高级 runner 暂不满足实验参数时，spec 要明确 helper 的职责，并保留结果结构。
