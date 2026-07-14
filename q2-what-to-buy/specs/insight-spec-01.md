# Insight: spec-01-signal-quality — 个股 vs ETF 信号质量对比

> **评分 38/55** · 修改后可发布；维度 4「可复现」与 6「抽象层次」是主要短板
> 评审基线：spec-review-handbook 11 维 rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q2 的**破冰 spec**，承担两项任务：① 让学员第一次接触 open-xquant 框架；② 用一次"反直觉实验"——同样的均线策略，5 只名股结果天差地别——把 q2 的核心命题"个股不如 ETF"立住。一份 spec 同时承载"框架引入 + 教学论证"两件事，是它复杂度高于 q1/spec-01 的根本原因。【教学场景】【结构】

**为什么挑这 5 只 A 股而不是更多/更少**：5 只是教学最优数 — 太少（如 2-3 只）样本量不够撑住"天差地别"的结论；太多（如 10 只）柱状图过于拥挤，且引入解释成本（为什么不选某只）。选茅台/五粮液（消费）、平安银行/招商银行（金融）、中国平安（保险）— 三大板块覆盖、全部是大盘蓝筹（学员耳熟能详）、结果离散度大，这是经过教学验证的"最少样本"。**但 spec 没解释这层选择**——【动机】缺位。

**为什么是 3 年而不是 5 年**：q1 用 5 年覆盖一个完整周期，q2 这里用 3 年，是因为本步**只是定性论证"个股嘈杂"**，3 年足够看出离散度，且与后续 q3-q9 的滚动窗口设定预热。但 spec 同样没写。

**spec 长度的张力**：85 行（含代码片段）远超 q1/spec-01 的 33 行。表面看违反【简洁】原则，但仔细看 — 大半行数花在 oxq 模块导入清单和回测构造细节上。这反映 q2 的硬约束：**学员第一次见到的 oxq 是一整块 ImportError 风险，spec 必须把模块路径全显式列出**。这是【教学场景：open-xquant 引入期】特有的临时复杂度，q3 起会简化。

**最大单点风险——没让 AI 先读 oxq 源码**：spec-writing-guide 原则 4「先读后写」明确要求"用到 oxq 时，spec 应在要求开头指示 AI 先阅读相关模块的源码"。本 spec 直接给出 8 个 oxq 模块的导入清单 + 完整的 `Strategy` / `Engine.run` 调用范式，等于把 oxq 接口"硬写"进 spec — 这正是 spec-writing-guide 警告的反例。当 oxq 升级（如 `Engine.run` 签名变化），整份 spec 失效。【教学场景】【可复现】

**回测调用范式不易于 0 基础学员理解**：要求第 6 条一次堆叠了 `signal.required_indicators` / `Strategy(signals=..., portfolio=...)` / `Engine.run(rules=[ExitRule(...)])` / `router=receiver=SimBroker()` 四套构造，没有 narrative 解释每一层在做什么。学员复制能跑通，但**仿写时无法理解**。这是【可学习】的硬伤。

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 起始日期为"3 年前"，结束日期为"当天" | `pd.Timestamp.now() - pd.DateOffset(years=3)` 动态计算 | spec 字面与 notebook 一致——但**两者都是反模式**：每次跑数据范围不同（同 q1/spec-01 的"时间炸弹"，且更严重） |
| 5 只 A 股代码 + 沪深300ETF | ✓ 字符级一致 | OK |
| `Crossover(fast="sma_1", slow="sma_20")` + `signal.required_indicators` 挂载 | notebook 实际写法是 `Crossover()` 然后赋值 `crossover_signal.required_indicators = {...}`；信号构造时 fast/slow 通过 `Strategy(signals={"cross": (crossover_signal, {"fast": "sma_1", "slow": "sma_20"})})` 传入 | spec 的 `Crossover(fast=..., slow=...)` 写法在 notebook 中**不存在**——【同步】严重违反 |
| `router` 和 `receiver` 使用同一个 `SimBroker()` | notebook 只用了 `broker = SimBroker()` 然后 `Engine().run(strategy, market=provider, broker=broker, ...)` — 没有 `router/receiver` 关键字 | spec 描述的接口与 notebook 实际接口**不一致**——【同步】违反 |
| 每只标的 `Strategy(name=...)` | notebook 用 `Strategy(name=f"ma-{symbol}", universe=StaticUniverse((symbol,)), ...)` — spec 没说 `universe` 参数 | AI 自行补全 `StaticUniverse`；spec 缺失关键参数 |
| 「个股年化波动率普遍在 XX%-XX%」 | notebook 用 `min(stock_vols)` / `max(stock_vols)` 动态填充 | OK |

**对照结论**：spec 与 notebook 在 **oxq 接口写法上有结构性漂移**，不是字面差异，而是**调用方式不同**。两份文件不是同一时间锁定的快照，spec 早于或晚于 notebook 一次重构。这是 q2 接入 oxq 期的典型"接口尚未稳态"症状，但暴露在面向学员的 spec 上是不能接受的。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 4 | "个股 vs ETF 对比"叙事清晰；但任务实际包含"导入 8 个模块 + 跑 6 次回测 + 画 2 张图"三件事 |
| 2 可验证性 | 3 | 有定性 oracle（柱状图 + 打印），缺机械断言（如 `assert len(results_ret) == 6`） |
| 3 输出契约具体度 | 4 | 颜色、figsize 都明确；缺收益率/波动率小数位、X 轴 grid alpha |
| 4 **可复现性** | **2** | **3 年前 → 今天**是动态时间窗，每次跑数据范围不同；oxq 版本未锁定 |
| 5 上下文 / 动机充分度 | 3 | 有"个股噪音 vs ETF"叙事，但 5 只标的的选择、3 年的时间窗都没解释 |
| 6 **抽象层次恰当** | **2** | **回测 6 步构造范式硬写进 spec**——把 oxq 接口当成"算法"写死，违反原则 4「先读后写」 |
| 7 正向指令为主 | 5 | 全部"做 X" |
| 8 结构一致性 | 5 | 严格四段 |
| 9 简洁性 | 3 | 50 行（不含代码块），但要求第 6 条嵌套 6 个子项过于密集 |
| 10 学员可学习性 | 3 | oxq 调用范式对 0 基础学员是"密码本"，仿写时不知道哪些参数是固定的、哪些是可换的 |
| 11 与 notebook 同步性 | 2 | `Crossover(fast=, slow=)` vs `crossover_signal.required_indicators=` / `router/receiver` vs `broker=` —— 两处接口字面级不一致 |
| **合计** | **38/55** | 修改后可发布；维度 4、6、11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：要求开头加「先读 oxq 源码」指令【教学场景】【可复现】

**现状**：要求第 2 条直接给出 8 个 oxq 模块的 import 清单 + 第 6 条把 `Strategy/Engine.run` 接口写死。

**改写**（在「## 要求」开头插入新的第 0 条）：
```
0. 先阅读 open-xquant 源码理解接口（再动手写代码）：
   - `oxq/core.py`：`Engine.run` 方法签名（参数顺序、关键字）
   - `oxq/signals/crossover.py`：`Crossover` 信号如何挂载 `required_indicators`
   - `oxq/portfolio/optimizers.py`：`EqualWeightOptimizer` 入场规则
   - `oxq/rules/exit_rule.py`：`ExitRule` 退出规则
   参考 https://github.com/xingwudao/open-xquant/tree/main/examples/tutorials
```

修复后 spec 不需要把接口硬写在第 6 条 — 让 AI 自己读源码理解。

### 改进 2：锁死 end_date 与 oxq 版本【可复现】

**现状**（要求 第 4-5 条）：
```
- 起始日期为 3 年前，结束日期为当天
```

**改写**：
```
- 数据时间窗：2023-01-01 ~ 2026-01-01（本课程数据快照截止日；与 q1 保持一致基准）
- open-xquant 版本：v0.x（写明本 spec 验证通过的版本号；后续升级时同步）
```

### 改进 3：spec ↔ notebook 接口对齐【同步】

**现状**：spec 说 `Crossover(fast="sma_1", slow="sma_20")`，notebook 说 `crossover_signal.required_indicators = {...}`。

**改写**（要求 第 6 条改为）：
```
6. 对每个标的，用 oxq 构建 Strategy 并跑回测：
   - 创建 Crossover 信号实例，挂载所需指标 sma_1（period=1）和 sma_20（period=20）
   - 用 StaticUniverse 把当前投资对象包成单一资产标的池
   - 用 Strategy + EqualWeightOptimizer 构建策略
   - 调用 Engine.run，传入 strategy/market/broker/start/end/rules，rules 包含 ExitRule
   - 从 result 取 total_return 和 annualized_volatility
```

不写具体调用语法，让 AI 读完源码自己写——这是「先读后写」的真正意义。

### 改进 4：补机械断言【验证】

**现状**：只有定性 oracle（柱状图 + 打印）。

**改写**（结果呈现 加新的第 0 条）：
```
0. 数据合法性检查：
   assert len(results_ret) == 6, "应有 5 只个股 + 1 只 ETF 共 6 个结果"
   assert "沪深300ETF" in results_ret, "结果中必须包含沪深300ETF 作为对照"
   assert all(0 < v < 1 for v in results_vol.values()), "年化波动率应在 0-100% 之间"
```

### 改进 5：把"为什么这 5 只 A 股 / 为什么 3 年"写进 spec【动机】

**现状**：标的清单和时间窗没解释。

**改写**（要求 第 5 条加注）：
```
5. 下载 5 只 A 股标的最近 3 年数据：
   ["600519.SS", "000858.SZ", "601318.SS", "000001.SZ", "600036.SS"]
   · 选 5 只：太少样本量不够，太多柱状图拥挤
   · 选这 5 只：消费（茅台/五粮液）+ 金融（中国平安/平安银行/招商银行），覆盖大盘蓝筹三大板块
   · 选 3 年：足以看出个股离散度，比 q1 的 5 年缩短一档（教学定性论证不需要完整周期）
```

让单读 spec 的学员就能 get 到这层选择背后的理由。

---

## 五、可沉淀的方法点（用于书中方法/模板章节）

> 标签体系：【结构】【精确】【可复现】【动机】【验证】【正向】【简洁】【同步】【可学习】【教学场景】

### A. 这份 spec 已经示范的原则

- **【结构】严格四段式**：上下文/任务/要求/结果呈现 — 与 q1/spec-01 一致，证明四段骨架可承载 q2 这种"框架引入 + 教学论证"的更复杂场景
- **【正向】全部"做 X"**：要求每条都是"导入 / 下载 / 构建 / 画图"动词起头，零否定堆叠
- **【教学场景：反直觉实验】**：用 5 只名股做对照实验得到"天差地别"的结论，是 q2 立论的核心。spec 在结果呈现段落里**预先把结论写出来**（"5 只个股的结果天差地别"），让学员看到柱状图时即刻确认实验意图——这是教学型 spec 的招式
- **【精确】配色规则显式**：沪深300ETF 蓝色 / 个股按正负绿红 / 波动率个股灰色 — 把视觉语义写死，避免 AI 每次自选颜色

### B. 这份 spec 修补后可示范的原则

- **【可复现】端日期锁死**：当前的"3 年前 → 今天"是动态窗口反模式；修复后可作为"任何相对时间窗都是反模式，必须显式锁端"的示范（与 q1/spec-01 「不指定结束日期」属于同一类反模式，但本 spec 的"起+终都是动态"更严重——证据强度更高）
- **【教学场景】oxq 引入期"先读后写"**：当前 spec 把 oxq 接口硬写在第 6 条；修复后可作为"用到框架时 spec 先指示 AI 读源码、不硬写接口"的示范，对应 spec-writing-guide 原则 4
- **【同步】spec/notebook 接口字符级对齐**：当前 `Crossover(fast=, slow=)` 与 `required_indicators=` 两种接口写法并存；修复后可作为"涉及具体接口调用时 spec 直接给可执行代码片段 = 跨文件零漂移"的示范
- **【动机】把"为什么挑这几个标的/这个时间窗"写进 spec**：当前缺位；修复后可作为"参数选择必须解释、不只是声明值"的示范（与 q1/spec-01 的"为什么选 510300"是同一类问题，本 spec 是"为什么选这 5 只"，证据强度叠加）
- **【验证】机械断言替代描述性"确保..."**：当前只有定性 oracle；修复后可作为"结果合法性 assert 替代'凭感觉看图'"的示范

### C. 领域 / 教学场景特殊考量

- **【教学场景】open-xquant 引入期 spec 的临时复杂度**：q2 是学员第一次见到 oxq，spec 不可避免要做"模块导入清单 + 接口范式介绍"。但**这两件事都不应该用「硬写代码」的方式做**，而应该用「先读源码 → 再写代码」的方式做。这是 spec-writing-guide 原则 4 的真正用武之地，本 spec 是测试该原则的第一个场景
- **【教学场景】"反直觉实验"型 spec**：q2/spec-01 不是"做事"型 spec，而是"用对照实验立论"型 spec。这类 spec 的特征：① 有明确论点（"个股嘈杂"）；② 通过对照组（5 只个股 vs 1 只 ETF）证明论点；③ 在结果呈现段落里**预先写好分析话术**（让学员看图后立刻验证论点）。这种"立论型 spec"是 q2-q9 的常见模式，需要在方法章节单独列出
- **【教学场景】跨章节"工具升级"过渡**：q1 用 yfinance 直取数据，q2 切到 oxq 的 `YFinanceDownloader` + `LocalMarketDataProvider` 的两步式数据访问。这种"工具升级断层"在课程中只发生一次（q1→q2），spec 里如何引导学员从"一行 download"过渡到"下载 + 读取分离"是一个独立的【教学场景】方法点，不是通用的 prompt 工程
