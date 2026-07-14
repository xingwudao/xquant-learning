# Insight: spec-04-rule-burden — 规则负担与自由度递增实验

> **评分 42/55** · 修改后可发布；维度 5「动机」与 3「输出契约」是高分项，9「简洁」与 11「同步」需修补
> 评审基线：spec-review-handbook 11 维 rubric
> 本文档定位：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q6 的收官 spec，也是全章最具教学野心的一份——它要让学员体会**前三步检验"参数选得对不对"，本 spec 检验"规则该不该加"**。"规则负担（Rule Burden）"是 Brian Peterson 框架中较少出现在通用资料里的概念——这正是【动机】维度的极佳测试：spec 必须**清晰定义"规则数"是什么、怎么数、阈值多少**，才能让 0 基础学员看懂这个非主流但关键的概念。【动机】【教学场景】

**"规则数"是什么**：spec 通过两个堆叠实验给出了清晰定义。
- **4A 规则堆叠**：Layer 0（基础策略）→ Layer 1（+ 调仓频率）→ Layer 2（+ 止损）→ Layer 3（+ 止盈）→ Layer 4（+ 移动止损）→ Layer 5（+ 最大回撤风控）。每层加**一条交易规则**，这是规则数的第一种含义。
- **4B 指标堆叠**：1 自由度（仅动量）→ 2（+ 波动率）→ 3（+ 调仓频率）→ 4（+ 止损）→ 6（+ 止盈 + 移动止损）。每层加**一个可优化参数**，这是规则数的第二种含义——"自由度"。

把"规则"和"自由度"分两个实验对比，**学员能看出"是规则本身的问题还是自由度的问题"**——这是本 spec 最巧妙的设计。【结构】【验证】

**阈值多少**：spec 没直接给数字阈值（如"自由度 ≤ 3 才安全"），而是让数据说话——4A 的样本内/样本外曲线分叉点、4B 的"边际收益消失"拐点，由 notebook 在分析段动态识别。这是符合"先猜后验，数据说了算"铁律的设计。【教学场景：实证主义】

**克制与张力**：spec 在 4B 的 E 配置（6 自由度）特意降到粗网格 `[10, 20, 30]`——避免组合数爆炸（5×5×4×6×5×5 = 15000 → 3×3×3×3×3×3 = 729）。这是【教学场景：算力预算】的好示范，但 spec 没写"为什么 E 用粗网格"——遗漏构成【动机】薄弱点。

约束的设计有金融语义：`StopLossRule.threshold < TakeProfitRule.threshold`（止损不应高于止盈）、`TrailingStopRule.trail_pct >= StopLossRule.threshold`（移动止损不应严于固定止损）、`MaxDrawdownRisk.max_drawdown >= StopLossRule.threshold`（组合层风控阈值不应小于个仓止损）——这些约束本身是金融领域知识，spec 把它们写在【精确】段是正确做法。【精确】【动机】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 4A 6 层、4B 5 层 | 字符级一致 | 良好 |
| Layer 5 最大回撤风控用 `MaxDrawdownRule(max_drawdown)` | notebook 用 `MaxDrawdownRisk(max_drawdown=...)`——**类名不一致** | spec 写的 `MaxDrawdownRule` 在 oxq 不存在；实际类是 `MaxDrawdownRisk`，违反【同步】 |
| 4A Layer 0 跑 `Engine().run(rules=[RebalanceFrequencyRule(interval_days=10)])` | notebook 通过 `run_layer` 函数，n_combos=1 时走单次回测分支 | 良好 |
| 4B E 配置粗网格 [10, 20, 30] | 字符级一致 | 良好；但 spec 没解释"为什么粗网格" |
| 引用 Brian Peterson"Rule burden is a form of overfitting" | notebook 出现完整引用（含 Peterson 第二段"Too many rules will make a backtest look excellent in-sample, and may even work in walk forward analysis, but are very dangerous in production."） | spec 写了引用一句，notebook 加了第二段——AI 自行补全（应进入 spec） |
| 没要求"参数判断"段 | notebook 有 80+ 行 4A 逐层增量判断 + 4B 边际效益拐点判断 + 综合建议 | spec 漏写（同 spec-01/02/03 模式）|
| 4A 图：双折线 + 衰减区域填充 | notebook 用 `fill_between(oos_sharpes, is_sharpes, alpha=0.15, color="red")` | spec 只说"双折线"，notebook 加了衰减区域填充——AI 自行补全 |
| `add_constraint("StopLossRule.threshold < TakeProfitRule.threshold")` | 字符级一致 | 良好 |
| `Engine().run(...)` 注意"构造函数无参数，rules 传入 run()" | notebook 写 `Engine().run(strategy, market=..., broker=..., start=..., end=..., rules=rules)`，符合 | 良好——这是 spec 给 AI 的关键提示 |
| run_layer 函数签名 `(layer_name, rules, paramset, description)` | notebook 实现一致 | 良好 |
| 总组合数（特别是 4A 各层） | spec 没要求打印组合数；notebook 在每层 print 里有 `{result_X['n_combos']}组合` | 部分契约 |

**对照结论**：本 spec 与 notebook 的同步度比 spec-02 / 03 都好，但 `MaxDrawdownRule` vs `MaxDrawdownRisk` 类名漂移是硬错误（学员复制 spec 给 AI 跑会找不到类）；参数判断段缺失是同章共性问题。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | "通过两个堆叠实验展示规则负担"任务一句话点明，4A/4B 两轴清晰 |
| 2 可验证性 | 4 | "4A 6 行 + 4B 5 行 + 各显示两条折线"机械验证；"4A 中样本内夏普随层数递增"是定性 |
| 3 输出契约具体度 | 4 | 6 层 / 5 层结构、字段、约束、figsize、双折线 + 标题都写得很细；缺参数判断段、衰减区域填充、Peterson 第二段引用 |
| 4 可复现性 | 4 | 复用 spec-01 的 IS_START/IS_END/OOS_START/OOS_END 锁死时段；TP/TRAIL/MAX_DD 阈值列表全锁死 |
| 5 **上下文 / 动机充分度** | **5** | **"前三步检验参数，本 spec 检验规则太多"承接清晰；4A/4B 双实验设计的动机也写了**——q6 章【动机】最高分 |
| 6 抽象层次恰当 | 4 | 用 `Engine().run(rules=[...])` 公开接口；但要求 1 写"确认 ParameterSet.add_constraint() 的约束表达式格式"——这是给 AI 的指令，应改成"先读 oxq.optimize.ParameterSet 源码" |
| 7 正向指令为主 | 5 | 全部"做 X" |
| 8 结构一致性 | 5 | 严格四段 + 验证段 |
| 9 **简洁性** | **3** | **107 行——q6 最长，4A 六层 + 4B 五层 + 两段约束让结构有重复感**（每层都重写参数空间） |
| 10 学员可学习性 | 4 | 4A/4B 双实验对学员是大量信息；run_layer 抽象帮助理解 |
| 11 **与 notebook 同步性** | **3** | `MaxDrawdownRule` vs `MaxDrawdownRisk` 类名漂移 + 参数判断段缺失 + Peterson 第二段引用未契约 |
| **合计** | **42/55** | 修改后可发布；维度 9 / 11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：修正 MaxDrawdownRisk 类名【同步】【精确】

**现状**（要求 1）：
```
- `oxq.rules.MaxDrawdownRule` — 最大回撤风控（`max_drawdown` 参数）
```

**改写**：
```
- oxq.rules.MaxDrawdownRisk — 最大回撤风控（max_drawdown 参数）
  · 注意类名是 MaxDrawdownRisk（风险规则），不是 MaxDrawdownRule
  · 在 oxq 中风险规则与交易规则分类不同——前者作用于组合层，后者作用于个仓
```

这是必须修的硬错误——直接影响学员能否跑通 spec。

### 改进 2：补"参数判断"段契约（增量评估 + 拐点识别）【同步】【精确】

**现状**：spec 完全没提"参数判断"，notebook 有 80+ 行。

**改写**（在要求 6 后新增）：
```
7. 参数判断（按 Peterson 增量评估原则）：
   
   7.1 4A 逐层增量评估：
   - 对 Layer 1 ~ Layer 5 逐层计算 (oos_sharpe[i] - oos_sharpe[i-1])：
     · 若改善 > 0.05 → 「✔ 可取」该规则
     · 若变化在 ±0.05 内 → 「⚠ 可选」效果存疑
     · 若恶化 < -0.05 → 「✘ 不可取」规则只帮了样本内
   - 找最佳层（样本外夏普最高的）→ 标注"超过这一层的规则都是规则负担"
   
   7.2 4B 边际效益判断：
   - 对配置 A→B / B→C / ... 逐层计算 is_gain 和 oos_gain：
     · 若 is_gain > 0.05 且 oos_gain < 0 → 标注"拐点：自欺欺人开始"
     · 若 oos_gain < is_gain × 0.3 → 标注"边际效益递减"
   - 找最佳自由度（样本外夏普最高）
   
   7.3 综合建议：
   - 规则选择：保留到最佳层 → 后续都是规则负担
   - 自由度控制：最佳自由度数量 → 更多 = 更多过拟合
```

### 改进 3：补 Peterson 第二段引用契约【同步】【精确】

**现状**（要求 6）：
```
- 引用 Brian Peterson 的观点：Rule burden is a form of overfitting
```

**改写**：
```
- 引用 Brian Peterson 的两段原话：
  · "Rule burden is a form of overfitting" — 规则负担本身就是一种过拟合
  · "Too many rules will make a backtest look excellent in-sample, 
    and may even work in walk forward analysis, 
    but are very dangerous in production."
- 用 print 完整输出英文 + 中译，让学员看到原文权重
```

### 改进 4：拆分要求段，引入子标题降低层数嵌套【简洁】【结构】

**现状**：要求 2 包含 6 层 4A、要求 3 包含 5 层 4B、每层都嵌套 paramset 定义——共三层嵌套。

**改写**（把要求段重构为四个明确块）：
```
## 要求

### 步骤 A：准备工作
1. 阅读 oxq.rules 模块（StopLossRule / TakeProfitRule / TrailingStopRule / MaxDrawdownRisk）
2. 定义新参数范围（TP_THRESHOLDS / TRAIL_PCTS / MAX_DD_VALS）
3. 编写 run_layer(layer_name, rules, paramset, description) 辅助函数

### 步骤 B：4A 规则堆叠（6 层）
4. 逐层定义 paramset 和 rules，调用 run_layer，结果存入 layers_4a
   [Layer 0 ~ Layer 5 各一行表格说明，附约束]

### 步骤 C：4B 指标堆叠（5 层）
5. 配置 A ~ E 各一行表格说明
6. E 配置用粗网格 [10, 20, 30]——避免 6 自由度组合数爆炸
   （细网格 5×5×4×6×5×5=15000 vs 粗网格 3^6=729）

### 步骤 D：分析、画图、判断
7. 汇总表 + 双图 + 参数判断 + Peterson 引用
```

### 改进 5：补 4B E 粗网格的"为什么"【动机】

**现状**（要求 3 的 E 项）：
```
E：+ 止盈 + 移动止损（6 个自由度，粗网格 [10,20,30]，约束 ...）
```

**改写**：
```
E：+ 止盈 + 移动止损（6 个自由度）
   · 粗网格：周期 [10,20,30] / 频率 [5,10,21] / 阈值 [0.03,0.07,0.15] / [0.10,0.20,0.30] / [0.05,0.10,0.15]
   · 为什么粗网格：6 个自由度若用 spec-01 的细网格组合数会到 15000+，
     回测耗时 > 半小时；粗网格在 729 组合内可在 5 分钟内跑完
   · 这是教学权衡：宁愿减少分辨率换取学员可接受的等待时间
```

---

## 五、可沉淀的方法点（用于书中方法/模板章节）

### A. 这份 spec 已经示范的原则

- **【动机】"前三步 vs 本 spec"的轴向切换**：要求段开头明说"前三步检验参数，本 spec 检验规则"——把 q6 四份 spec 的逻辑关系显式化。可作为"章末 spec 应总结全章逻辑结构"的【结构】高分例证
- **【结构】4A/4B 双实验对照**：把"加规则"和"加自由度"分两个实验跑，让学员能区分"是规则的问题还是自由度的问题"。可作为"实证型 spec 的双实验设计"的示范
- **【精确】带金融语义的约束链**：`StopLoss < TakeProfit`、`TrailingStop >= StopLoss`、`MaxDrawdown >= StopLoss` 三组约束本身是领域知识。可作为"约束写法 = 嵌入领域知识"的示范
- **【教学场景：实证主义】不给数字阈值，让数据说话**：spec 没写"自由度 ≤ 3 才安全"这类硬阈值，而是让 notebook 通过增量评估动态识别。可作为"避免硬编码领域结论 = 鼓励学员看数据"的示范
- **【精确】Engine 接口的关键提示**：要求 1 末尾"`Engine().run(...)` 注意：构造函数无参数，rules 传入 run()"是给 AI 的关键提示——规避了 oxq 早期版本 Engine 接口变动的常见错误。可作为"spec 应给 AI 标注框架易错点"的示范

### B. 这份 spec 修补后可示范的原则

- **【同步】oxq 类名漂移检测**：当前 `MaxDrawdownRule` vs `MaxDrawdownRisk` 是命名漂移。修复后可作为"spec 中所有类名 / 参数名都应来自 oxq 源码 grep，不能凭记忆"的示范——值得做工具化检查（可写脚本 grep `oxq.rules.*Rule|Risk` 与 spec 比对）
- **【简洁】堆叠型 spec 的层次分组**：当前 4A 六层各自重写 paramset，结构有大量重复。修复后可作为"堆叠型 spec 应抽出共有结构、各层只写差异"的示范
- **【动机】粗/细网格的算力权衡**：当前 E 用粗网格但没解释。修复后可作为"性能敏感的 spec 必须显式说明权衡"的【教学场景】示范
- **【同步】权威引用必须完整契约化**：当前 Peterson 第二段引用在 notebook 但 spec 只写第一段。修复后可作为"权威引用应字符级写入 spec，避免 AI 自行补全产生不准确版本"的示范

### C. 领域 / 教学场景特殊考量（不通用但必须教）

- **【教学场景】"规则负担"是金融领域少见的概念**：通用 ML 领域有"模型复杂度 / 正则化"，但很少把"业务规则数"和"参数自由度"分开数；金融场景下"规则数 ≠ 参数数"——例如止损规则只有一个 threshold 参数（1 自由度），但它本身是一条独立规则（占 4A 的一层）。本 spec 把两者分开数是金融领域的关键教学点，可在书中方法章节专门写一节"什么是规则、什么是自由度、为什么要分开数"
- **【教学场景】Peterson 增量评估原则**：通用 ML 的 ablation study 也做"加 / 减组件看效果"，但很少明确写"每加一个组件必须独立证明 OOS 价值"这种规范。Peterson 的增量评估是金融策略开发框架特有的——本 spec 通过 4A 逐层判断显式应用了这个原则，是【教学场景】的高质量素材
- **【教学场景】组合数爆炸的现实约束**：本 spec 是 q6 章第一次明确提及"组合数 × 折数 × 时间 = 真实算力成本"——通用 ML 教学很少提及这种现实约束（有云算力可挥霍）。学员用本地笔记本跑 q6，必须理解粗 / 细网格的权衡。可作为"工具链约束 = spec 必须考虑的非功能性需求"的示范
- **【教学场景】"Rule burden" 中文译法的塑造**：本 spec 是中文量化教学第一次把这个概念译为"规则负担"——这种术语本地化本身是【教学场景】的产出。可在书中方法章节附"q6 引入的金融术语对照表"
