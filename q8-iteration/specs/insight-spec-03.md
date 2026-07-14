# Insight: spec-03-iteration — 怎么改？假设驱动的对照实验

> **评分 43/55** · 修改后可发布；维度 4「可复现性」与 9「简洁性」是修补重点
> 评审基线：11 维 spec rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标。Per-spec 学员引导不在此文范围

---

## 一、设计意图复盘

这是 q8 收官 spec，也是全书"假设驱动迭代"方法论的总集示范——把"观察 → 假设 → 验证标准 → 实验 → 结论"的闭环具象化为两轮对照实验。spec 巧妙地把第一轮设计成"假设被推翻"（调仓频率改不动高波动表现），第二轮设计成"假设被确认"（波动率过滤有效）——一推一立，让学员体会"推翻不是失败而是学习"的心智。这种**故意安排"先错后对"叙事**的教学设计，在本课程其他章节少见，是 q8 独有的【教学场景】特征。【动机】【教学场景：失败示范】

**为什么用 Strategy.hypothesis / objectives 字段**：不是单纯写在注释里。spec 第 27、37 行明确要求"创建 Strategy 时填写 hypothesis 和 objectives 字段"——这把"假设驱动"从方法论层面落到代码契约层面。学员复制 spec 跑出来的 Strategy 对象自带 .hypothesis 属性，这种"机器可读的实验记录"思路是 oxq 的设计创新。【教学场景：oxq 抽象】【精确】

**【可学习】维度的关键测试——"看情况调整"vs"具体准则"**：这正是 handbook 关键提示里点名的——迭代 spec 的【可学习】维度成败在于"是不是给学员具体判断准则"。这份 spec 在迭代 1 给了清晰准则："主目标：高波动时段的夏普比率优于基准（21 天）；约束：全时段最大回撤不恶化超过 2 个百分点"；迭代 2 也清晰："主目标：最大回撤改善 ≥ 30%；约束：夏普比率不低于 1.0"。**这是这份 spec 最大的亮点**——它没说"看情况调整频率"，而是说"用以下两条标准判断假设是否成立"。这份 spec 把【可学习】拉到了高分。【可学习】【验证】

**【精确】维度的隐患——"最佳配置"判定逻辑没显式**：迭代 2 第 41 行 spec 说"测试 4 种配置：无过滤、阈值 10%、15%、20%"——但选哪一个作为"最佳配置"去对照基准？notebook 第 16 cell 的实现是"回撤改善最好的"（best_improve 最大化）。spec 没说选择标准——是按回撤选？按夏普选？按综合？这种"选择函数"留给 AI 是【精确】的隐患。【精确】

**配色 / 加粗 / 图例标注的细节程度**：spec 第 33 行明确要求"21 天行标注'-- 基准'"、"21 天加粗"、"图例标注'高波动夏普'而非全时段夏普"——这种**显式打架的图例细节**让人欣赏。但配色（`['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71', '#3498DB', '#9B59B6']` 6 色）spec 没指定，notebook 自选。【精确】半到位。

**实验记录表的落地：ExperimentLog**：spec 第 49 行用 `ExperimentLog.add()` 把两轮迭代记录下来——这是把"假设驱动方法论"沉淀为"机器可读历史"的最后一步。比起前面章节让学员手抄 markdown 笔记本，这种 oxq 抽象更可持续。【教学场景】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 6 种频率（5/10/15/21/42/63） | ✓ 字符级一致 | 高 |
| 21 天加粗 + 标注"-- 基准" | ✓ lw=2.5 vs 1.5；marker = " ← 基准" | 一致；但 spec 说 "-- 基准"、notebook 用 " ← 基准"，符号不同——【同步】偏差 |
| 图例标注高波动夏普 | ✓ `f'{freq}天（高波动夏普 {d["hv_sharpe"]:.2f}）'` | 一致 |
| iter1 假设验证打印引导 | ✓ "注意：我们的假设是'改善高波动期表现'..." | 一致 |
| 4 种配置：无过滤、10%、15%、20% | ✓ vol_thresholds = [None, 0.10, 0.15, 0.20] | 一致 |
| `VolFilteredOptimizer` 来自 oxq | spec 第 22 行说"oxq.portfolio.optimizers.VolFilteredOptimizer"，但 notebook 第 16 cell 实际**自己定义了** VolFilteredOptimizer 类 | **严重【同步】偏差**——spec 假设 oxq 已实现，notebook 实际 reimplement |
| ExperimentLog 字段：name, observation, hypothesis, criteria, result, conclusion, notes | ✓ notebook 第 18 cell 字符级一致 | 高 |
| Trade-off 分析：年化收益降低多少换回撤改善多少 | ✓ 第 16 cell 末尾打印 | 一致 |
| 保存 iter1_results / iter2_results / best_label / best_improve / best_freq_hv / best_hv_sharpe / dd_limit | ✓ notebook 都已定义 | 一致 |

**对照结论**：**最严重的【同步】偏差是 VolFilteredOptimizer**——spec 说从 oxq 导入，notebook 自己 implement。两种可能：① oxq 还没实现这个类（spec 在驱动 oxq 升级，符合 MEMORY.md 里"课程驱动 open-xquant 同步开发"原则）；② oxq 已实现但 notebook 漂移没用。无论哪种，**spec 与 notebook 字符级不一致**，违反【同步】维度核心原则。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 4 | 三件事（迭代 1 + 迭代 2 + 记录表）紧耦合，叙事自然；可拆分但代价更大 |
| 2 可验证性 | 4 | 验证段有"6 种频率指标表完整""4 种配置指标表完整""2 行迭代记录"，机械可数；缺 assert |
| 3 输出契约具体度 | 4 | 表格列名 / 图例标注 / 加粗规则全明确；缺配色锁定 |
| 4 **可复现性** | **3** | end=today 时间炸弹延续；oxq 版本未声明；VolFilteredOptimizer 是否在 oxq 中存在不确定 |
| 5 上下文 / 动机充分度 | **5** | 假设 / 验证标准都解释清楚；ExperimentLog 的"为什么记录"也说了——这份 spec 的【动机】维度是 q8 三份里最强的 |
| 6 抽象层次恰当 | 4 | hypothesis / objectives / VolFilteredOptimizer / ExperimentLog 都用 oxq 抽象；但"最佳配置选择函数"留给 AI |
| 7 正向指令为主 | 5 | 全部 "做 X"，无否定句 |
| 8 结构一致性 | 4 | 四段式遵循；【要求】段内分迭代 1 / 2 / 记录表三层结构跟 spec-02 同模式 |
| 9 简洁性 | **3** | 62 行偏长；迭代 1 / 2 内部步骤密度高，可压缩共性配置（broker / 引擎 / 评估）到顶层 |
| 10 学员可学习性 | **5** | 验证标准给得具体（"≥ 30% / ≥ 1.0"），不是"看情况调整"——这是 q8 三份 spec 中【可学习】最强的一份 |
| 11 与 notebook 同步性 | 2 | VolFilteredOptimizer 字符级不一致；"-- 基准" vs " ← 基准"小偏差；配色靠 AI |
| **合计** | **43/55** | 修改后可发布；维度 4、9、11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：澄清 VolFilteredOptimizer 的实际位置【同步】【教学场景】

**现状**（spec 第 22 行）：
```
- oxq.portfolio.optimizers — RiskParityOptimizer、VolFilteredOptimizer（包装器，高波动期将权重缩放 0.5）
```
（但 notebook 实际自己定义了这个类，spec 与 notebook 严重不一致）

**改写**（两种方案择一，看 oxq 实际状态）：

**方案 A**（如 oxq 已实现 VolFilteredOptimizer）：
```
- oxq.portfolio.optimizers — RiskParityOptimizer、VolFilteredOptimizer
- 注：VolFilteredOptimizer(base_optimizer, vol_threshold, market_vol) — 包装任意 optimizer，
  当 market_vol 当日值超过 vol_threshold 时将所有非 CASH 权重 × 0.5，剩余归入 CASH
- notebook 与 spec 字符级一致：from oxq.portfolio.optimizers import VolFilteredOptimizer
```

**方案 B**（如 oxq 尚未实现，notebook 是参考实现）：
```
- oxq.portfolio.optimizers — RiskParityOptimizer
- 注：本 spec 需要 VolFilteredOptimizer 包装器（高波动期权重 × 0.5 + 剩余归 CASH）。
  open-xquant 当前版本尚未提供，请先在 notebook 中定义参考实现：
  ```python
  class VolFilteredOptimizer:
      def __init__(self, base_optimizer, vol_threshold, market_vol):
          ...
      def optimize(self, signals, indicators):
          # 取 indicators 最新日期对应的 market_vol
          # 若超阈值，所有非 CASH 权重 × 0.5，剩余归 CASH
          ...
  ```
  下个版本 oxq 会把这个类内置。
```

无论哪种方案都比当前"暧昧不一致"好——【同步】维度从 2 分提到 5 分。

### 改进 2：锁死 end_date【可复现】

**现状**（spec 第 8 行）：
```
- 已定义的变量：result_base、equity、daily_ret、detector、...
```
（间接依赖 spec-01 的 today，时间炸弹延续）

**改写**：
```
- 数据范围：与 spec-01、spec-02 一致，end=2026-01-01（课程数据快照截止日）
- 这是迭代实验，必须在固定数据范围内对照；动数据范围 = 不同迭代结果不可比
```

接续型 spec 链有同源【可复现】问题——本份 spec 是终端，必须显式承接。

### 改进 3：显式锁定"最佳配置选择函数"【精确】

**现状**（spec 第 45 行）：
```
- 假设验证：检查最佳配置是否满足两个验证标准
```
（"最佳配置"是按什么标准选的？回撤？夏普？综合？没说）

**改写**：
```
- 选择"最佳配置"的标准（必须显式）：
   best_label = argmax(dd_improvement)  # 在三个非基准配置中，选回撤改善最大者
   即：iter2_results 中除"无过滤"外，1 - max_dd / base_dd 最大的那个
- 验证标准检查：
   pass_dd = best_improve >= 0.30
   pass_sharpe = iter2_results[best_label]["sharpe"] >= 1.0
   conclusion = "确认" if (pass_dd and pass_sharpe) else "部分确认" if pass_dd else "推翻"
```

让 AI 不用揣摩"最佳"的含义——这是【精确】维度的关键修补。

### 改进 4：压缩 iter1 / iter2 共性配置到顶层【简洁】

**现状**：iter1 / iter2 都写"`Engine.run()` 传入 `rules=make_rules()`"、"`SimBroker(fee_model=FEE_MODEL, fill_price_mode=FillPriceMode.NEXT_OPEN)`"、"打印净值对比图（figsize 14×7）"——重复 4-5 次。

**改写**（加到 spec 开头新增"共性配置"段）：
```
共性配置（迭代 1 / 2 / 后续都用）：
- broker：`SimBroker(fee_model=FEE_MODEL, fill_price_mode=FillPriceMode.NEXT_OPEN)`
- 净值图：figsize=(14, 7)，基准（21 天 / 无过滤）加粗 lw=2.5、其他 lw=1.5
- 配色：6 色循环 ['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71', '#3498DB', '#9B59B6']
- 图例格式：'{label}（高波动夏普 {x.xx}）' 或 '{label}（夏普 {x.xx}）'
```

把共性提炼到顶层，让迭代 1 / 2 各步骤聚焦于差异点，spec 整体瘦身约 20%。

### 改进 5：补 ExperimentLog 字段值的字符级锁定【精确】【同步】

**现状**（spec 第 50 行）：
```
- 用 log.add() 添加两轮迭代的记录（name、observation、hypothesis、criteria、result、conclusion、notes）
```
（具体每个字段填什么没说）

**改写**：
```
- 用 log.add() 添加两轮迭代的记录：
   迭代 1：
     name="iter1-rebal-freq"
     observation="高波动期表现差"
     hypothesis="缩短调仓频率能改善高波动期表现"
     criteria={"high_vol_sharpe": "above_baseline", "max_dd_limit": float(dd_limit)}
     result={"best_freq": int(best_freq_hv), "best_hv_sharpe": float(best_hv_sharpe)}
     conclusion="rejected"
     notes="最优频率更长而非更短，改执行参数没用"
   迭代 2：
     name="iter2-vol-filter"
     observation="高波动时策略满仓暴露在风险中"
     hypothesis="高波动时自动降仓位能显著降低回撤"
     criteria={"dd_improvement": ">=30%", "sharpe": ">=1.0"}
     result={"best_config": best_label, "dd_improvement": f"{best_improve:.1%}", "sharpe": float(iter2_results[best_label]["sharpe"])}
     conclusion="confirmed"
     notes="用收益换安全的 trade-off"
```

这是迭代记录表的核心产出，必须字符级显式——"看图自己揣摩"留太多 AI 自由度。

---

## 五、可沉淀的方法点（用于书中方法/模板章节）

> 标签体系（10 个）：【结构】【精确】【可复现】【动机】【验证】【正向】【简洁】【同步】【可学习】【教学场景】

### A. 这份 spec 已经示范的原则

- **【可学习】验证标准必须具体到数字**：iter1 的"高波动夏普 ≥ 基准"、iter2 的"回撤改善 ≥ 30% 且夏普 ≥ 1.0"——不是"看情况调整"，而是"事前定好阈值"。这是迭代 spec 跟"调参 spec"的本质差异，可作为方法章节"假设驱动 = 验证标准事前锁定"原型。**这条方法点是 q8 全章最重要的产出**
- **【动机】先错后对的叙事编排**：iter1 故意被推翻、iter2 被确认——这种教学编排把"假设被推翻是好事"的心智从抽象主张落到具体体验。值得作为方法章节"教学故事弧线设计"示范
- **【精确】Strategy.hypothesis / objectives 字段把假设落到代码契约**：让"假设驱动"从口号变成机器可读字段——其他章节的 spec 也可以效仿"把方法论沉淀到代码契约"的思路
- **【正向】全 "做 X"**：spec 全文无 "不要"句式
- **【教学场景：oxq 抽象】ExperimentLog 把记录沉淀为机器可读历史**：跟 spec-01 / spec-02 的 StrategyMonitor / MarketStateDetector 同源思路——本课程"运维原语 oxq 化"的设计哲学
- **【精确】图例标注规则显式**："21 天加粗""图例标注高波动夏普而非全时段夏普"——这种主动避免 AI 在视觉细节上自由发挥的写法，是【精确】维度的好示范

### B. 这份 spec 修补后可示范的原则

- **【同步】oxq 是否已实现的"待开发"标记**：当前 VolFilteredOptimizer 来路不明（spec 假设 oxq 实现，notebook 自己写）；修复后的"如已实现 / 如未实现"双轨写法可作为"课程驱动框架升级时的 spec 写法"示范——这呼应 MEMORY.md 里"课程需要什么 oxq 就更新什么"的协作模式
- **【可复现】接续型 spec 链的终端必须显式承接前序 spec 的所有【可复现】约束**：当前 end=today 时间炸弹通过变量继承隐性传递；修复后可作为"接续链终端 spec 的可复现承接"示范
- **【精确】"最佳配置"选择函数必须显式**：当前留给 AI 揣摩；修复后的 `argmax(dd_improvement)` 显式可作为"模糊选择函数的 spec 反模式"示范
- **【简洁】共性配置提炼到顶层**：当前 broker / 净值图配色 / 图例格式在 iter1 / iter2 重复多次；修复后可作为"长 spec 的共性提炼"原则示范
- **【精确】ExperimentLog 字段值字符级锁定**：当前 spec 只列字段名；修复后的字符级具体值可作为"机器可读输出 = 字段值必须显式"示范

### C. 领域 / 教学场景特殊考量（不通用但必须教）

- **【教学场景】"先错后对"的迭代故事弧**：迭代 1 故意被推翻、迭代 2 被确认——这种叙事编排在普通技术教程几乎不见。本课程把"假设驱动迭代"教成方法论时，必须示范"推翻不是失败"——而最有效的示范方式就是 spec 主动安排一次推翻。值得作为方法章节"教学示范的张力设计"原则
- **【教学场景】"执行参数"vs"策略逻辑"的认知拆分**：iter1 改频率（执行参数）→ 推翻；iter2 改优化器（策略逻辑）→ 确认。这种认知拆分（"多久行动"vs"做什么")比起单纯讲"调参"深一层——它指向"哪类参数改了有用、哪类没用"的元认知。本课程在迭代 spec 里把这层元认知显式化是必要的领域教学
- **【教学场景】oxq 协同进化的 spec 写法**：spec-03 涉及 VolFilteredOptimizer / ExperimentLog 等可能尚未在 oxq 中固化的抽象——MEMORY.md 已说明"课程需要什么 oxq 就更新什么"。spec 应当显式标记"这个抽象在 oxq 当前版本是 / 不是已有"，避免学员复制 spec 跑不通时陷入混乱。这是普通技术教程不需要的"教程 vs 框架协同进化"维度
- **【教学场景】触发条件 / 频率 / 阈值【精确】度的运营章特征**：q8 三份 spec 都涉及"周期性运营任务"。监控（spec-01）的【精确】是告警阈值；诊断（spec-02）的【精确】是判定阈值；迭代（spec-03）的【精确】是验证标准——三者都是"事前锁定数字阈值"的同源方法点。这是 q8 / q9 章独有、前 7 章不需要的领域骨架，是运营章 spec 与建造章 spec 的核心差异
