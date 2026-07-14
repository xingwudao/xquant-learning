# Insight: spec-03-alpaca-paper — 回测 vs 实盘，差距有多大？Alpaca 模拟交易

> **评分 43/55** · 修改后可发布；维度 4「可复现」与 6「抽象层次」需重点修补
> 评审基线：spec-review-handbook.md 11 维 rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标。

---

## 一、设计意图复盘

这是 q7 章**最有挑战的一份 spec**——同时要满足三个相互拉扯的约束：① 让有 Alpaca 账号的学员体验真实下单（关键的"震撼瞬间"）；② 让没账号的学员也能完成完整流程（不能因为外部依赖卡死大多数学员）；③ 不能把 API key 写进任何文件（安全底线）。spec 用 Part A / B-1 / B-2 三段切分 + 环境变量检测 + try/except 兜底实现这种平衡。【结构】【教学场景：实盘严肃性】

**为什么必须有 LiveBroker 这一段**：spec-01/02 都是 SimBroker 估算，spec-03 如果还是 SimBroker，q7 整章就还是回测——学员体验不到「策略真的下了一笔单」的震撼。Alpaca paper trading 是免费的、可逆的、隔离的——是 0 基础学员第一次接触真实订单接口的最佳沙盒。这是 q7 章无法妥协的设计核心。【动机】【教学场景】

**为什么 Part B-1 和 B-2 不可省略**：spec 第 2 步明确「Part A、Part B-1、Part B-2 缺一不可」。B-1 只对比数据源差异（Alpaca IEX vs YFinance），B-2 才是真实下单。把数据源差异和真实下单分开，让学员看到**两层执行落差**——数据层 + 真实成交层。这种切分反映了 spec-02 的"积分式归因"思想在 spec-03 的延续。【结构】

**API key 处理的三重防线**：① 环境变量 `os.environ.get("ALPACA_API_KEY")`，spec 第 4 步显式说不传参；② 整段包 try/except，连接失败自动切换；③ 验证段倒数第二条「不包含任何硬编码的 API Key」是显式的安全检查。这是 q7 章实盘严肃性最关键的工程规矩。【精确】【可复现】【教学场景：实盘严肃性】

**A 股 → 美股的标的切换说服**：q1-q6 + q7 spec-01/02 都用 A 股 ETF。spec-03 突然切到美股（SPY/QQQ/GLD），上下文段说"open-xquant 内置了 Alpaca 美股模拟交易接口"——清晰交代切换原因。spec-04 还会继续美股、然后桥接 A 股结尾。这种「主线 A 股 → 中段切美股做实验 → 结尾桥回 A 股」的叙事是 q7 整章的标的物结构。【动机】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 三段切分（A / B-1 / B-2） | ✓ 字符级一致 | 一致 |
| 环境变量 `ALPACA_API_KEY` 检测 | ✓ `HAS_ALPACA = bool(os.environ.get("ALPACA_API_KEY"))` | 一致 |
| `AlpacaClient(paper=True)` | ✓ | 一致 |
| `AlpacaMarketDataProvider(feed="iex")` | spec 写 `feed="iex"`；notebook `AlpacaMarketDataProvider()` 默认值 | spec 与 notebook 表面不一致，但 oxq 默认值 = iex（需验证） |
| `time.sleep(3)` 等待成交回报 | ✓ | 一致 |
| `live_broker.close()` 关闭连接 | ✓ | 一致 |
| `plot_sim_vs_live` 公共函数 | ✓ | 一致 |
| 无账号替代方案：NEXT_OPEN + 滑点 | ✓ | 一致 |
| Engine.setup + step 逐 bar | ✓ | 一致 |
| 美股佣金率 | spec 没指定具体值，notebook 用 `Decimal("0.001"), min_fee=Decimal("1")` | spec 缺 |
| `latest_prices` 取数 fallback 到"最近一个交易日" | notebook 有 `recent = alpaca_market.get_bars(sym, start="2026-03-01", end=today)` | spec 描述模糊（"最近一个交易日"）→ notebook 写死 2026-03-01，硬编码日期 |
| 图片保存路径 | `../book/images/04-data-source-comparison.png` | spec 缺 |
| 滑点对比的"回测价"语义 | notebook 用 `latest_prices.get(symbol)` 作为回测价 | 概念上不严谨——"回测价"应是 result_sim 里同标的同日的成交价，不是当日最新价。spec 不够明确导致 AI 简化处理 |

**对照结论**：三段切分的骨架对齐良好；但**美股佣金率、价格 fallback 的具体写法、图片路径、"回测价"语义**四处由 AI 自行补全。其中 fallback 写法 `start="2026-03-01"` 是硬编码日期，违反 q1/insight-spec-01 强调的"任何固定日期都需 spec 明确"。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | "三段切分 + 缺一不可"明确 |
| 2 可验证性 | 5 | 验证段最严格——明确列出"必须包含的全部三部分输出"，且包含"不包含任何硬编码 API Key"的安全断言 |
| 3 输出契约具体度 | 3 | 三段输出明确；但美股佣金率、price fallback 写法、图片路径、滑点计算的"回测价"语义都缺 |
| 4 可复现性 | 2 | **end="今日" 时间炸弹**；oxq 版本未声明；外部 API（Alpaca）行为变化无版本锁；fallback 用硬编码日期；feed="iex" 默认值假设 |
| 5 上下文 / 动机充分度 | 5 | 上下文段明确"前两步是估算，现在体验真实下单"；标的切换说服强 |
| 6 抽象层次恰当 | 3 | **多处实现细节越权**：spec 第 6 步细节（手动写 print 格式、try/except 每笔订单、time.sleep(3)）已经接近代码翻译；好的 spec 应该说"打印订单提交确认 / 等待成交后查询"，让 AI 决定细节 |
| 7 正向指令为主 | 5 | 全部"做 X" |
| 8 结构一致性 | 5 | 严格四段 + 验证段 |
| 9 简洁性 | 3 | **101 行** 是 q7 四份 spec 里最长的；要求段第 6 步嵌套了 11 个子项目的微指令，可压缩 30 行 |
| 10 学员可学习性 | 4 | 上下文叙事清晰；但 oxq.contrib.alpaca / LiveBroker / Engine.setup+step 等专业 API 名密度高 |
| 11 与 notebook 同步性 | 3 | 价格 fallback 的具体写法、图片路径、佣金率漂移 |
| **合计** | **43/55** | 修改后可发布；维度 4 / 6 / 9 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：锁 end 日期 + 锁 oxq 版本 + 锁 alpaca-py 版本【可复现】

**现状**：spec 用 `start="2021-01-01", end=今日`，oxq 和 alpaca-py 版本都没声明。涉及外部 API 的 spec 而无版本锁是高风险。

**改写**（要求段第 1 条上方加）：
```
**版本与时间锁**：
- open-xquant >= 0.7.0（含 Alpaca contrib 模块）
- alpaca-py >= 0.30.0（Alpaca 官方 SDK）
- 数据时间窗：start="2021-01-01"，end="2026-01-01"
- LiveBroker 实际下单的"今日"价格 = 实盘运行时刻；其余历史数据全部锁死
```

声明边界：哪些是历史可复现的、哪些是实盘随机的（学员理解会更清晰）。

### 改进 2：抽象层次回归——把 B-2 的细节交给 AI【抽象层次】【简洁】

**现状**（spec 第 6 步 11 个子项）：
```
- 打印分隔线和标题"LiveBroker 实盘演示：..."
- 用 AlpacaClient.get_positions() 获取当前持仓，打印每个标的的股数和成本价
- 用 AlpacaClient.get_account() 获取账户权益
- ... （省略 8 项）
- 等待 3 秒后调用 live_broker.get_fills()
- 调用 live_broker.close() 关闭连接
- 用 AlpacaClient.get_positions() 查看最终持仓
```

太多实现细节。这违反 q1/insight-spec-01 已总结的"写做什么 + 关键参数，不越权规定算法"。

**改写**：
```
6. **Part B-2——LiveBroker 实盘演示**（有 Alpaca 时执行）：
   核心动作：
   a. 读取当前持仓 + 账户权益（用 AlpacaClient）
   b. 用最新价 + generate_orders 算调仓订单（lot_size=1）
   c. 如有订单，用 LiveBroker.submit_order 逐笔提交
   d. 等待 3 秒后用 live_broker.get_fills() 查成交
   e. 打印对比表（标的/方向/股数/成交价/回测价/滑点）
   f. 收尾：live_broker.close() + 打印最终持仓

   边界条件：
   - 无需调仓时打印"无需调仓"并跳过下单
   - 没有成交时（市场关闭）查询订单状态
   - 整段包 try/except，失败转 Part 7 兜底
```

抽象到「核心动作 + 边界条件」，让 AI 决定打印格式、try/except 细节。

### 改进 3：明确"回测价"的语义【精确】

**现状**：spec 写"成交价、回测价（最新收盘价）、滑点"——把"回测价"等同于"最新收盘价"。但严格意义上，回测价应是 `result_sim.trades` 里同标的同日的 `filled_price`。

**改写**：
```
e. 滑点对比表的语义：
   - 成交价：LiveBroker 实际成交的价格
   - 回测价：当下使用的最新收盘价（即 generate_orders 输入的 prices）
     · 此处不是 result_sim 里的历史成交价，因为 LiveBroker 是当下下的单
   - 滑点：(成交价 - 回测价) / 回测价
```

避免 AI（和读者）误解"回测价"的来源。

### 改进 4：price fallback 的具体写法【精确】【同步】

**现状**：spec 写"如果当天无数据，用最近一个交易日的收盘价"——描述模糊。notebook 实际写死 `start="2026-03-01"`。

**改写**：
```
- 取最新价：
  · 优先用 alpaca_market.get_bars_multi(symbols, start=END, end=END)
  · 如该日无数据（周末/节假日），回溯到 END 之前 30 个自然日窗口取最后一根 bar：
    recent = alpaca_market.get_bars(sym, start=(END - timedelta(days=30)), end=END)
    latest = Decimal(str(recent.iloc[-1]["close"]))
```

把"最近一个交易日"翻译成可执行的回溯窗口。

### 改进 5：补 figsize / 图片路径 / 美股佣金率【同步】【精确】

**改写**（要求段补一条）：
```
**美股交易常量**：
- 佣金率：PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("1"))（千一佣金，美股标准）
- 滑点：PercentageSlippage(rate=Decimal("0.001"))
- 数据源：YFinance（Part A）/ Alpaca IEX（Part B-1，feed="iex" 显式传入）
- 图片保存：../book/images/04-data-source-comparison.png（dpi=150）
```

---

## 五、可沉淀的方法点

### A. 这份 spec 已经示范的原则

- **【结构】"基准 → 数据差 → 真实下单"三段递进**：Part A 建立基准、Part B-1 揭示数据源差异、Part B-2 真实下单——这种切分让学员看到**两层执行落差**（数据层 + 真实成交层），是「积分式归因」在执行场景的应用
- **【精确】API key 处理三重防线**：环境变量 + try/except + 验证段安全断言——可作为「涉外部 API 的 spec」的安全模板
- **【动机】无账号替代方案明确**：spec 第 7 步把"没 Alpaca 怎么办"完整设计为 NEXT_OPEN + 滑点的 SimBroker 模拟——确保 100% 学员都能完成。这是 0 基础课程的关键关怀
- **【教学场景】公共绘图函数抽取**：`plot_sim_vs_live` 同时服务 Part B-1（数据源对比）和 Part 7（无账号兜底）——可作为"跨场景可视化复用"模板
- **【教学场景：实盘严肃性】验证段最严格**：明确「不包含任何硬编码 API Key」+ 「输出必须包含全部三部分」——这种强约束是其他章节没有的，反映 q7 实盘严肃性

### B. 这份 spec 修补后可示范的原则

- **【可复现】涉外 API 的 spec 必须三锁**：oxq 版本 + alpaca-py 版本 + 数据时间窗——当前缺位；修补后可作为「外部依赖 spec 的版本锁模板」
- **【抽象层次】实盘下单流程的"核心动作 + 边界条件"抽象**：当前 spec 第 6 步太细；修补后可作为「Part B-2 应该写成什么样」的 before/after 示范，是抽象层次的典型教学案例
- **【精确】"回测价"语义必须显式**：当前隐含等同最新价，修补后可作为"涉及多概念的字段必须 spec 内消歧"的示范
- **【简洁】控制 spec 长度的折叠技巧**：把 11 个子项压成 6 个核心动作 + 3 个边界条件——可作为"长 spec 重构"的教学案例

### C. 领域 / 教学场景特殊考量

- **【教学场景：实盘严肃性】API key 安全是不可妥协的工程底线**：q7 是学员第一次面对真实可花钱的接口。即使是 paper trading，养成"绝不硬编码 key"的习惯是关键。spec 用三重防线（env var + try/except + 验证段断言）把这条规矩内化到操作流程里
- **【教学场景：外部依赖的兜底设计】**：q1-q6 spec 都假设学员能跑通核心流程。q7 spec-03 必须接受"少数学员没 Alpaca 账号"的现实——spec 第 7 条的 NEXT_OPEN+滑点替代方案是 q7 唯一一份「双轨 spec」。这种设计模式在涉及外部账号 / 网络 / 付费服务的 spec 中应推广
- **【教学场景：A 股 → 美股的标的切换叙事】**：q7 章前两 spec 用 A 股、spec-03 切美股、spec-04 桥回 A 股。这不是工程随意——是 open-xquant 当前只内置 Alpaca 美股 paper trading，国内券商接口尚未集成。spec-03 上下文段必须诚实交代这个限制，避免学员误解"美股才有 paper trading"
- **【教学场景：Engine.setup + step 模式的引入】**：Part B-1 用 `Engine.setup() + Engine.step(date)` 而不是 `Engine.run()`——为后续 q8 的实时增量回测做铺垫。spec 应明确这层"为什么不用 run"的动机，避免学员看到两个不同 API 困惑
