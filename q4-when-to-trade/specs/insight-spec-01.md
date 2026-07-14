# Insight: spec-01-rebalance-frequency — 调仓频率对比 + 引入交易成本

> **修补后状态：可发布** · 已同步固定截止日与新版 SDK 接口；保留原评审要点作为方法复盘
> 评审基线：spec-review-handbook 11 维 rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q4 的第一份 spec，承担**双重破冰**任务：① 把"调仓频率"这个隐性参数显化为可对比的实验；② 第一次把"交易成本"纳入回测。两件事单拎出来都够独立写一份 spec，合并在一起是因为没有成本的频率对比毫无意义——frequency 的核心代价就是手续费，分开讲会让"频率为什么是个权衡"这个核心论点失去抓手。【教学场景：实验设计】

**为什么选风险平价（RiskParity）作为基础信号**：上下文里点明"始终持有全部 3 只 ETF，方便观察止损和止盈规则的效果"——这是为整章做的铺垫。q4 后两个 spec 要对比"加止损/止盈 vs 不加"的差异，如果基础信号在某些 bar 上空仓，止损/止盈就没有持仓可触发，对比会因样本稀疏而失真。这种"为后续 spec 选基础信号"的考量，是接续型 spec 链特有的设计。【动机】【教学场景：跨 spec 接续】

**为什么 FREQUENCIES = [5, 10, 21, 63]**：每周 / 两周 / 每月 / 每季度。spec 主体没显式解释这四个数字的来源，但可以反推——交易日下 5/10/21/63 是常用的"周/双周/月/季"近似（A 股一年约 252 个交易日）。这四个值覆盖"很勤"到"很懒"的连续光谱，又不像 1/3/126/252 那样太极端。**问题是 spec 没把这层解释写进去**——学员仿写换标的时，可能误以为这四个数是某种"标准答案"。【动机】

**run_backtest 辅助函数的提取**：spec 第 5 条用代码块定义了 `run_backtest(frequency, fee_model, order_rules)`。这个函数会被 spec-02 / spec-03 复用——是接续型 spec 链的"接续接口"。spec 没把这一点显式地说出来（只在结尾"供后续 spec 复用"半句话提了），但这是整章三份 spec 的关键架构决策。【结构】【教学场景：接续型 spec 链】

**两轮回测的 narrative 张力**：第一轮不含成本，第二轮含成本。这种"先理想后现实"的对比是教学设计的精华——单纯讲"频率越勤成本越高"是说教，先让学员看到"理想中频率确实有差"，再加成本看排名是否会颠覆，才是有戏剧张力的实验。【动机】【教学场景：渐进难度】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| `signal = Threshold()` + `signal.required_indicators = {...}` | 实际写在 `run_backtest` 函数内部，每次调用都新建 signal | 已同步，避免跨调用状态污染 |
| 新版 SDK 回测调用 | 实际是 `Engine().run(strategy, market=..., broker=..., start=..., end=..., rules=...)` | 已同步 |
| `portfolio = RiskParityOptimizer(...)` | 实际放在 `Strategy(...)` 内联构造 | 已同步 |
| Strategy 字段 `signals + portfolio + name + universe` | 实际包含 `name=f"freq-{frequency}"` 和 `universe=universe` | 已同步 |
| 总手续费 `sum(float(f.fee) for f in result.trades)` | 实际是 `sum(float(f.fee) for f in r.trades)` | 已同步，避免 Decimal 格式化问题 |
| 净值曲线 figsize 12x6 | ✓ | 一致 |
| 4 条线归一化到 100 | ✓ | 一致 |
| 「频率越高，交易越多，成本越大」 | ✓ 字符级一致 | 一致 |
| 共同交易日处理（消除中美日历差异） | notebook 实际做了 `common_trading_days` 交集计算 | 已同步 |
| 固定数据窗口 | spec 与 notebook 均使用 `START = "2021-01-01"`、`END = "2026-03-18"` | 已同步 |
| 含手续费 broker 语义 | notebook 使用 `BookCompatibleSimBroker` 复现书中原实验口径 | 已同步 |

**对照结论**：spec-01 已按 notebook 的新版 SDK 用法修补：固定 `END = "2026-03-18"`，补共同交易日处理，`run_backtest` 改为 `Engine().run(...)` 语义，并用 `BookCompatibleSimBroker` 保持书中原实验的手续费口径。原问题可作为"spec 内嵌接口示例容易随 SDK 迭代漂移"的方法复盘。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | "对比 4 种频率 + 引入成本"叙事清晰 |
| 2 可验证性 | 4 | 验证段有"无成本/含成本各 4 行 + 净值图 4 条线 + 手续费递增"机械判据 |
| 3 输出契约具体度 | 4 | 表格列名、figsize、颜色、归一化基准全明确；缺 X/Y 轴标签、grid alpha |
| 4 **可复现性** | **4** | 已锁定 `END = "2026-03-18"`；仍可补 oxq 版本声明和参数来源解释 |
| 5 上下文 / 动机充分度 | 4 | 选 RiskParity 解释清晰；FREQUENCIES 四个数字未解释来源 |
| 6 抽象层次恰当 | 4 | run_backtest 是恰当的抽象；但内嵌大段代码块（5/8 条）轻度越权 |
| 7 正向指令为主 | 5 | 全做 X，分析段唯一一处「不要硬写'更高'或'更低'」是合理的反模式提醒 |
| 8 结构一致性 | 5 | 严格四段（含验证），子段命名规范 |
| 9 简洁性 | 4 | 100 行偏长但每条都"删了就坏"——内嵌代码块占用大量行 |
| 10 学员可学习性 | 5 | 全程零金融黑话，"调仓频率""交易成本"都用大白话解释 |
| 11 与 notebook 同步性 | 5 | 新版 SDK 调用、`common_trading_days`、`float` 转换均已同步 |
| **合计** | **51/55** | 可发布；剩余改进集中在参数来源解释和机械自检 |

---

## 四、可改进点（带改写示例）

### 改进 1：锁死回测结束日期【可复现】

**现状**（要求 第 4 条）：
```
- 数据起始日期 START = "2021-01-01"
```

**改写**：
```
- 数据起始日期 START = "2021-01-01"
- 数据结束日期 END = "2026-03-18"（本课程数据快照截止；后续所有图表与回测数字以此为基准）
- 在所有 downloader.download / get_bars / engine.run 调用中显式传 end=END，不要使用动态当前日期
```

否则学员 2027 年跑出来的频率排名可能和书上对不上——q4 是接续型 spec 链的源头，源头漂移会污染后续两个 spec。

### 改进 2：解释 FREQUENCIES 四个数字的来源【动机】

**现状**（要求 第 6 条）：
```
6. 定义 4 种调仓频率：FREQUENCIES = [5, 10, 21, 63]，分别对应约每周、两周、每月、每季度。
```

**改写**：
```
6. 定义 4 种调仓频率：FREQUENCIES = [5, 10, 21, 63]
   · 5 ≈ 每周（A 股一周约 5 个交易日）
   · 10 ≈ 两周（即 Q3 用的默认值）
   · 21 ≈ 每月（A 股一年约 252 个交易日 / 12 月 ≈ 21）
   · 63 ≈ 每季度（252 / 4 = 63）
   选这四个值是为了覆盖"很勤"到"很懒"的连续光谱。学员仿写时可换成 [3, 7, 14, 30] 等，
   只要保持"周/月/季"层级跨度即可。
```

让学员理解"为什么是这四个数"，仿写时不会误以为是固定答案。

### 改进 3：spec 中 oxq 接口示例与实际签名对齐【同步】

**修补前问题**（要求 第 5 条内嵌代码）：
```python
broker = BookCompatibleSimBroker(fee_model=fee_model) if fee_model else SimBroker()
return Engine().run(
    strategy,
    market=LocalMarketDataProvider(),
    broker=broker,
    start=START,
    end=END,
    rules=rules,
)
```

**改写**：
```
5. 定义 run_backtest(frequency, fee_model=None, order_rules=None) 辅助函数，封装策略
   构建和回测执行。具体接口签名以 oxq 源码为准（见步骤 2「先读源码」），
   函数应支持：
   - 输入：调仓频率（int 天数）、可选费用模型、可选额外规则列表
   - 内部：构造 Strategy（含 signals + portfolio + universe + name），构造 SimBroker，
     调用 Engine().run(...)，传入 rules=[RebalanceFrequencyRule(interval_days=frequency), *order_rules]
   - 返回：result 对象（带 .total_return / .max_drawdown / .sharpe_ratio / .trades / .equity_curve）
```

把"具体怎么调"留给 AI 看源码定，spec 只声明语义契约——这才是【先读后写】的正确写法。

### 改进 4：补一个机械可验证的 assert【验证】

**现状**：验证段只描述"对比表有 4 行 + 手续费随频率递增"。

**改写**（移到结果呈现后，加一节"自检"）：
```
0. 自检（执行后立即验证）：
   assert len(results_no_fee) == 4 and len(results_with_fee) == 4, "应生成 4 个频率的结果"
   fees_sorted = [sum(float(f.fee) for f in results_with_fee[freq].trades) for freq in FREQUENCIES]
   # 频率索引升序对应天数 [5, 10, 21, 63]——天数越大手续费应越小
   assert fees_sorted == sorted(fees_sorted, reverse=True), \
       f"手续费应随频率间隔增大而减小，实际：{fees_sorted}"
```

让"频率越高成本越大"从描述变成机械判据。

### 改进 5：补 common_trading_days 预处理【同步】【精确】

**现状**：spec 没提中美日历差异处理。

**改写**（加到要求第 4 条数据加载后）：
```
- 因 510300（上交所）与 513100（纳指 ETF，跟踪美股节假日）日历不同，构造 common_trading_days：
  common = mktdata[SYMBOLS[0]].index
  for sym in SYMBOLS[1:]:
      common = common.intersection(mktdata[sym].index)
  后续画图时所有 equity_curve 都 reindex(common).dropna() 后归一化。
```

否则净值曲线归一化时，不同标的的缺失日期会导致曲线断裂。

---

## 五、可沉淀的方法点

> 标签体系：【结构】【精确】【可复现】【动机】【验证】【正向】【简洁】【同步】【可学习】【教学场景】

### A. 这份 spec 已经示范的原则

- **【结构】辅助函数提取作为接续型 spec 链的接口**：`run_backtest` 在 spec-01 定义、spec-02/03 复用——这是"多份 spec 串成实验链"的关键架构。可作为方法章节"接续型 spec 链如何设计接口"的原型。
- **【动机】两轮实验的 narrative 张力**：先无成本看理想，再含成本看现实。这种"理想 vs 现实"的双轮设计是优秀的教学叙事，可作为"如何让对比实验有戏剧性"的示范。
- **【教学场景】先读后写指示完整列出 oxq 模块**：要求第 2 条把 5 个 oxq 类全部点名（`PercentageFee`/`SimBroker`/`RebalanceFrequencyRule`/`RiskParityOptimizer`/`Engine`+`Strategy`），让 AI 读完源码再动手——比"先阅读 oxq 源码"一句话强得多。可作为"先读后写指示要细到模块级"的示范。
- **【正向】"动态描述方向，不要硬写'更高'或'更低'"**：要求第 10 条这条反模式提醒，避免 AI 把分析写死成"频率 5 比频率 10 收益更高"——结果会随数据日期变。可作为"分析文字应根据实际数据生成"的示范。
- **【可学习】零金融黑话**：通篇用"调仓频率""交易成本""每 5 天调一次"的大白话；唯一专业术语"夏普比率"是 q3 已介绍。0 基础学员能直接读懂。

### B. 修补后可示范的原则

- **【可复现】end 日期锁死**：q4 是接续链源头，源头不锁后续全漂。修补后可作为"接续型 spec 链的源头必须最严格锁时间"的原型。
- **【动机】参数列表必须解释来源**：当前 `FREQUENCIES = [5, 10, 21, 63]` 没说为什么是这四个数；修补后可作为"参数选择必须给出反推逻辑"的示范。
- **【同步】spec 里的接口示例代码与实际签名漂移**：SDK 迭代后，spec 中写死的接口示例容易过期；修补后可作为"spec 内嵌代码块是双刃剑——能写清意图但容易与实现漂移，最好让 AI 先读源码"的反例转正。
- **【验证】机械 assert 替代描述性"手续费递增"**：当前只有验证段描述；修补后可作为"对比实验的核心规律应该写成 assert"的示范。
- **【精确】跨市场标的必须做日历对齐**：common_trading_days 预处理 spec 漏写；修补后可作为"多标的回测的领域必备预处理"的示范。

### C. 领域 / 教学场景特殊考量

- **【教学场景】oxq 框架特有的"先读后写"**：从 q4 起 spec 大量调用 oxq，spec 写法的最佳实践是"列出要读的模块清单 + 只声明语义契约 + 不写死接口签名"。这是本课程独有的——通用 prompt 工程不需要面对"框架在迭代"这个张力。spec-01 在"列出模块清单"上做得好，但在"不写死接口签名"上失分（要求第 5 条直接内嵌 Engine 构造代码）。
- **【教学场景】接续型 spec 链的"源头 spec"责任更重**：q4 三份 spec 串成一个实验链——spec-01 的 `run_backtest`、`results_with_fee`、`FREQUENCIES`、`FEE_MODEL` 都被后两份 spec 引用。源头 spec 的可复现性、命名稳定性比独立 spec 要求更高。这是接续型 spec 链特有的，应在方法章节单独列出。
- **【教学场景】首次引入"成本"的克制**：spec 第一次引入 `PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5"))`——A 股万分之十佣金 + 5 元最低（实际 A 股最低 5 元起步）。这两个数没解释来源，但选了符合 A 股现实的参数（不是简单 0.1% 或 0.5%），是默默植入的领域知识。可作为"领域参数即知识"在方法章节强调——和 q1/insight-spec-01 的"实现细节就是知识"互证。
