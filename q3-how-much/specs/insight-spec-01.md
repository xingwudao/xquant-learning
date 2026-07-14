# Insight: spec-01-equal-weight — 等权组合：仓位分配的破冰起点

> **评分 42/55** · 修改后可发布；维度 4「可复现性」与 11「同步性」是修补重点
> 评审基线：q1/insight-spec-01 同款 11 维 spec rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q3 章首份 spec，承担**仓位分配的破冰**作用——学员第一次理解"权重不是 0/1 二值，而是一组求和为 1 的小数"。spec 选择最朴素的等权方案（各买 1/3）作为起点，给后两份 spec（风险平价、动量排名）留出难度阶梯：等权 → 引入波动率 → 引入排序。这条递进与"先猜后验"的认知节奏完全吻合，是优秀的渐进式教学设计。【结构】【教学场景：渐进难度】

**为什么用 oxq 框架**：q3 起课程引入 open-xquant，spec 第 2 步明确列出 8 个 oxq 模块要求 AI 先读源码（`EqualWeightOptimizer / Threshold / RollingVolatility / Engine / Strategy / RebalanceFrequencyRule / SimBroker / YFinanceDownloader / LocalMarketDataProvider / StaticUniverse`）。这条「先读后写」是 spec-writing-guide 原则 4 的首次大规模实战——避免 AI 用过时接口编造代码。【教学场景：oxq 框架】

**为什么三只 ETF 维持 q2 选择**：`SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")` 直接接续 q2 的"全球宏观三资产"。这条接续在 spec 上下文段写得清楚（"Q2 选好了 3 只 ETF"），让读者立刻明白 q3 是 q2 的延续而非另起。【结构】跨章衔接是仓位分配章的天然优势——上一章已选好标的，本章只需关注权重。

**等权权重的精确性悖论**：spec 要求"打印权重的具体含义——10 万元换算"，等权下三只各 33,333 元。本应是输出契约最稳妥的部分，但 spec **没明确写"权重和=1.0±1e-6"的断言**——这条仓位分配 spec 的灵魂校验缺位，AI 自行补全的可能性低，留下隐患。【验证】

**结果呈现的克制与张力**：spec 末尾打印的三句分析（"波动差了 N 倍"/"等权一样多"/"有没有更聪明的分法"）是认知钩子，刻意为 spec-02 风险平价铺垫。这种"在 spec 里写明引出下一份的悬念"是仓位分配三联 spec 的连贯利器，但也带来风险——分析话术固化在 spec 里，notebook 实际数据若与"差了 N 倍"不符就会冲突。当前实现用 f-string 动态填充（`{max(vols)/min(vols):.1f} 倍`），优雅地化解了这个矛盾。【动机】【同步】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 起始日期 `2021-01-01`，结束日期"为当天" | `today = pd.Timestamp.now().strftime("%Y-%m-%d")` | **时间炸弹**：同一份 spec 不同日跑结果不同，违反【可复现】 |
| `Threshold` 信号 `column="close", threshold=0, relationship="gt"` | 字符级一致 | 严格同步 |
| 8 个 oxq 模块"先读源码" | notebook 直接 `from oxq...` 导入使用 | spec 教学指示无法在 notebook 中验证（合理：notebook 是产物，不是过程） |
| 「为每只 ETF 预计算 20 日滚动波动率（后面 spec-02 会用到）」 | spec-01 的 cell 没用到 vol；spec-02 的 cell 才在 `signal_rp.required_indicators` 里设 vol | spec 的"预计算"承诺与 notebook 实际"按需在 signal 上设"不一致——违反【同步】 |
| `RebalanceFrequencyRule(interval_days=10)` | 一致 | 同步 |
| 三只 ETF 单独持有指标 vs 等权组合 | 一致 | 同步 |
| 净值曲线 figsize 12×6，三灰一蓝 | 实际 styles `--/:/-.` + 三种灰阶 + `#4472C4` | 同步，且补全了具体色号 |
| 标题「各买三分之一：等权组合 vs 单只持有」 | 字符级一致 | 同步 |
| 末尾分析三句 | f-string 动态填充 `min/max/差几倍/最大波动名` | spec 写大意，notebook 用动态填充——优秀的【同步】策略 |
| 验证段「等权权重每只约 33.3%」 | notebook 没有 assert | 验证写在 spec 里却没有机械断言，AI 自行选择跳过 |
| 共同交易日处理（中美交易日历差异） | notebook 有 `common_trading_days = ... .intersection(...)` | spec 完全没提，AI 自行补全——这是金融跨市场场景的关键技巧 |

**对照结论**：spec 大方向覆盖完整，但**两处关键漂移**：① 结束日期不锁定 ② "预计算波动率"承诺与 notebook 实际不符 ③ 共同交易日处理（多市场 ETF 必备）spec 没提。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | 「等权回测 + 三 ETF 表现差异」紧耦合，叙事自然 |
| 2 可验证性 | 4 | 验证段有定性 oracle（"权重约 33.3%"），缺机械 assert（如 `assert abs(w.sum()-1)<1e-6`） |
| 3 输出契约具体度 | 4 | 标题/列名/figsize/线型全明确，缺权重数值类型与求和精度 |
| 4 **可复现性** | **2** | **结束日期 = 当天** 是时间炸弹，未声明 oxq / yfinance 版本 |
| 5 上下文 / 动机充分度 | 5 | 上下文清晰承接 q2，"为什么从等权开始"自洽（最简单做对照） |
| 6 抽象层次恰当 | 5 | 不规定 EqualWeightOptimizer 内部算法，只给参数与组装方式 |
| 7 正向指令为主 | 5 | 全部"做 X"，无否定堆叠 |
| 8 结构一致性 | 5 | 严格四段（上下文/任务/要求/结果呈现）+ 验证段，符合课程模板 |
| 9 简洁性 | 4 | 95 行偏长，但每条都有承担——12 步要求确实是 12 件不同的事 |
| 10 学员可学习性 | 4 | 可读，但 oxq 模块 8 个并列让 0 基础学员容易眼花 |
| 11 与 notebook 同步性 | **3** | "预计算 vol"承诺漂移 + 共同交易日处理 spec 未提 + 末尾分析话术与动态实现略偏 |
| **合计** | **42/55** | 修改后可发布；维度 4、11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：锁死 end_date，消除"当天"陷阱【可复现】

**现状**（spec 第 5 条）：
```
使用 YFinanceDownloader 下载 3 只 ETF 数据（起始日期 2021-01-01，结束日期为当天）。
```

**改写**：
```
使用 YFinanceDownloader 下载 3 只 ETF 数据：
- 起始日期：2021-01-01
- 结束日期：2026-01-01（本课程数据快照截止日；后续所有图表与回测数字以此为基准）
```

修复成本极低，q1/q2 同款修复理由——同一原则在 q3 反复出现，证据更足。

### 改进 2：补一个权重和的机械 assert【验证】【教学场景：仓位分配特殊】

**现状**：spec 验证段只描述"每只约 33.3%"，没机械断言。

**改写**（加到结果呈现 第 0 条）：
```
0. 权重合法性检查：
   weights = ew_weights_df.iloc[-1]
   assert len(weights) == 3, f"应有 3 只 ETF 权重，实际 {len(weights)}"
   assert abs(weights.sum() - 1.0) < 1e-6, f"权重和应为 1.0，实际 {weights.sum()}"
   assert (weights >= 0).all(), "等权权重不应为负"
```

**仓位分配 spec 的灵魂断言**就是"权重和=1.0"，这条 assert 在三个 spec 中都该有——后续 spec-02/03 应当复用同一断言模板。

### 改进 3：共同交易日处理写进 spec【精确】【同步】【教学场景：跨市场】

**现状**：spec 没提中美交易日历差异，notebook 自行补 `common_trading_days = mktdata[SYMBOLS[0]].index.intersection(...)`。

**改写**（加到要求 第 12 条净值曲线之前）：
```
12. 计算共同交易日（中美交易日历不同步会让净值出现锯齿）：
    common_trading_days = mktdata[SYMBOLS[0]].index
    for sym in SYMBOLS[1:]:
        common_trading_days = common_trading_days.intersection(mktdata[sym].index)
    后续所有净值曲线、权重历史图都用此索引对齐。
```

这是跨市场 ETF 组合的必备技巧，0 基础学员永远想不到——必须写进 spec。

### 改进 4：「预计算波动率」承诺要么兑现要么删【同步】

**现状**（要求 第 7 条）：
```
使用 LocalMarketDataProvider 加载数据，并为每只 ETF 预计算 20 日滚动波动率（后面 spec-02 会用到）。
```

但 notebook 中 spec-01 的 cell 不用 vol，spec-02 才在 `signal_rp.required_indicators` 里按需设。spec 的"预计算"是个空头支票。

**改写**（删除"预计算"承诺）：
```
7. 使用 LocalMarketDataProvider 加载数据为字典 mktdata（key=symbol，value=DataFrame）。
   注：滚动波动率不在此预计算，而是在 spec-02 中通过 signal.required_indicators 按需注册。
```

显式说明波动率的注册时机，避免 spec-01 与 spec-02 的接续含糊。

### 改进 5：oxq 模块「先读源码」可分组减负【可学习】【教学场景：oxq】

**现状**：spec 第 2 条罗列 8 个并列模块，0 基础学员看了发懵。

**改写**：
```
2. 阅读以下 oxq 模块源码（按用途分四组）：
   ① 引擎与策略：oxq.core.Engine, oxq.core.Strategy
   ② 数据：oxq.data.YFinanceDownloader, oxq.data.LocalMarketDataProvider
   ③ 仓位优化：oxq.portfolio.optimizers.EqualWeightOptimizer
   ④ 信号与规则：oxq.signals.Threshold, oxq.indicators.RollingVolatility,
      oxq.rules.RebalanceFrequencyRule, oxq.universe.StaticUniverse, oxq.trade.SimBroker
   先理解每组的输入输出，再动手组装。
```

分组 + 注释让 8 个模块的认知负担降一半。

---

## 五、可沉淀的方法点（用于书中方法/模板章节）

> 标签体系（10 个）：【结构】【精确】【可复现】【动机】【验证】【正向】【简洁】【同步】【可学习】【教学场景】

### A. 这份 spec 已经示范的原则

- **【结构】跨章接续骨架**：上下文段直接承接 q2 的标的池，让 q3 是 q2 的延续而非另起 — 仓位分配章的天然优势，可作为「跨章节 spec 接续」的方法素材
- **【教学场景：oxq 框架】「先读源码」首次大规模实战**：spec 第 2 条要求 AI 先读 8 个 oxq 模块再写代码 — q3 起 oxq 介入后这条原则的标杆示范，可作为「oxq spec 必含先读后写」的范例
- **【动机】认知钩子写进 spec 末尾**：「波动差了 N 倍 / 等权一样多 / 有没有更聪明的分法」三句话固化在 spec 里，承担 spec-01 → spec-02 的过渡 — 可作为「连续 spec 链中如何写过渡话术」的范例
- **【正向】全部"做 X"**：12 步要求全部正向指令 — q1 同款，证据再积累一次

### B. 这份 spec 修补后可示范的原则

- **【可复现】「结束日期为当天」即时间炸弹**：当前 spec-01 第 5 条直接写"结束日期为当天" — 修复后作为「任何'当天/最新'都是反模式」的多章证据（q1+q3 同款问题强化）
- **【验证】仓位分配 spec 的灵魂断言「权重和=1.0」**：当前 spec 没有机械 assert — 修复后作为「领域特殊验证模板」的标杆（不写不知道，写了就跑不偏）
- **【同步】「预计算 X，后面 Y 会用到」即漂移源**：spec-01 第 7 条承诺预计算波动率，notebook 实际在 spec-02 才注册 — 修复后作为「跨 spec 资源承诺要么兑现要么删」的反模式
- **【精确】跨市场必备的共同交易日处理**：spec 漏写，notebook 自行补 — 修复后作为「领域必备配置块」（类似 q1 的字体三选一），可在方法章节单列"中美 ETF 组合 spec 必含交易日对齐"

### C. 领域 / 教学场景特殊考量（不通用但必须教）

- **【教学场景：仓位分配】权重向量的输出契约特殊性**：仓位分配 spec 的所有产出都包含「权重向量」（每标的占比，求和=1）。这是与 q1 单标的 spec 的最大区别。spec 必须显式：① 权重向量的形状与列名；② 权重和=1 的精度（1e-6）；③ 权重数值范围（[0,1]）。这是仓位分配章的「领域必备验证模板」
- **【教学场景：oxq 框架】8 个模块并列的认知负担**：q3 起 oxq 介入，spec 中模块罗列容易让 0 基础学员发懵。**spec 应按用途分组**（引擎 / 数据 / 优化器 / 信号规则）— 这是 oxq spec 写作的特殊考量，可作为「oxq spec 模块罗列方法点」单列
- **【教学场景：跨市场组合】中美交易日历差异**：本章三只 ETF 跨上交所与美股市场，自动产生交易日历不同步。spec 必须显式给共同交易日交集的代码片段（`intersection`），不能让 AI 自行猜。这是 q3+ 章节相比 q1 的新约束 — 单标的章节不需要，跨市场章节必须教
