# Insight: spec-01-benchmark-and-metrics — 跟什么比？基准与风险调整指标

> 2026-07-11 复现迁移备注：执行 spec 与 notebook 已修复为固定窗口
> `START = "2021-01-01"`、`END = "2026-03-18"`，并使用
> `BookCompatibleSimBroker` 复现书中原实验语义。下文保留的是迁移前评审脉络，
> 其中关于动态日期和接口漂移的条目已作为本次修复依据。

> **评分 41/55** · 修改后可发布；维度 4「可复现」与 2「可验证」是修补重点
> 评审基线：handbook 11 维 rubric + q1/insight-spec-01 样品
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q5 的开篇 spec,承担**给"好不好"装一把尺子**的核心教学任务。前四章学员一路看到"年化 15%、夏普 0.8"的数字,但从未问过这些数字"贵不贵"——本章的破冰就是把"等权买入持有三只 ETF"这个朴素基准摆到对比表的最后一行,让数字有了参照物。【动机】【教学场景】

**为什么选四个策略一起对比**:EqualWeight、RiskParity、TopNRanking、RP+止损 5%——这是 Q3-Q4 全部"产出物"的合集。spec 不引入新的策略,而是把前四章的产出**集中送进体检台**。这个选择极其克制:学员认知负担只在"评估方法"这一条线上,不需要再消化新的策略逻辑。【教学场景:渐进难度】

**为什么用三把尺子(夏普/卡玛/索提诺)而不是只夏普**:本节的二级教学目标是建立"风险有多个维度"的认知。spec 在要求 2 列出三个比率的**完整接口**,并在分析(要求 12)指示 AI"夏普看总波动,卡玛看最大回撤,索提诺只看下行波动"——这是把概念锚定到指标公式上,而不是停留在词汇层。【动机】

**oxq 接口先读后写**:要求 2 和要求 5 两次指示 AI"先阅读源码",分别针对 RunResult 的评估方法和 portfolio optimizers 的构造参数。这是 q2 起 open-xquant 集成原则的标准实践——比 q1 那种"硬写代码"的反例进了一大步。【教学场景:open-xquant 框架】

**克制点与张力**:spec 没有给夏普比、卡玛比、索提诺比的**具体计算公式**——只给中文名+一句话描述,完全依赖 oxq 的接口实现。这是好处也是隐患:好处是 spec 不与库实现耦合,框架升级 spec 不变;隐患是学员复制 spec 后无法独立验证 oxq 计算的对错(比如年化方法是 252 还是 365、用算术均值还是几何均值)。【精确】维度因此扣分。

---

## 二、与迁移前 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| `data 起始 2021-01-01,无 end_date` | `today = pd.Timestamp.now().strftime("%Y-%m-%d")` 动态取今天 | **时间炸弹**——同份 spec 不同日期跑出不同数据范围,违反【可复现】 |
| `run_strategy(portfolio, indicators, freq=10, stop_loss=None)` 函数签名 | notebook 实现的 indicators 是 dict(`{"vol": (RollingVolatility(), {...})}`),不是 spec 写的 list(`[RollingVolatility(period=20)]`) | spec 与 notebook 数据结构不一致,**严重违反【同步】** |
| 要求 9「价格归一化到 1,等权平均」 | `eq_bh_norm = eq_bh_prices.div(eq_bh_prices.iloc[0]); eq_bh_portfolio = eq_bh_norm.mean(axis=1)` | 字符级一致 |
| 对比表 5 行 × 8 列 | 5 行(4 策略+基准)、8 列(策略名+7 指标) | 一致 |
| 净值曲线归一化到起点 = 100 | `equity / equity.iloc[0] * 100` | 一致 |
| 三把尺子的"冠军对比" | notebook 多输出 `if len({sharpe_best, calmar_best, sortino_best}) > 1: print("不同的尺子给出了不同的冠军!")` | spec 没要求,AI 自行补全(教学价值高) |
| `figsize=(12, 6)` | ✓ | 一致 |
| **没要求 figsize 之外的网格/格式** | `ax.grid(True, alpha=0.3); ax.axhline(y=100)` | spec 缺失,AI 主动补全;下次重跑可能不同 |
| 基准的 sharpe 公式 | `(eq_bh_daily_ret.mean() * 252) / (eq_bh_daily_ret.std() * np.sqrt(252))` | spec 没给公式,AI 自己推导;**与 oxq 的 sharpe 公式可能不同口径** |

**对照结论**:spec 大方向覆盖完整,但 (a) 时间锁缺失、(b) indicators 数据结构 list vs dict、(c) 基准指标的计算公式没显式化——三处隐患都触发"重跑结果不一致"风险。

---

## 三、最佳实践对照(11 维 rubric)

| 维度 | 分(1-5) | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | "运行四策略+构造基准+对比表+曲线图"虽多但都在"对比"主题下 |
| 2 **可验证性** | **3** | 验证段只说"5 行 8 列、4 实线 1 虚线、超额有正负",**没机械 assert**(如 `assert len(comparison_df) == 5; assert len(comparison_df.columns) == 8`);更关键是**没验证指标值的合理范围** |
| 3 输出契约具体度 | 3 | 列名/图例位置精确,但**指标的精度(.2% vs .2f)、表格分隔符、对齐方式**没明说,AI 自由发挥 |
| 4 **可复现性** | **2** | 没锁 end_date(notebook 用 `today` 取当前日期)、没声明 oxq 版本、没声明三把尺子的年化方法(252 还是 365) |
| 5 上下文/动机充分度 | 5 | 「年化 15% 好不好取决于市场」「Beta vs Alpha」「三把尺子各看什么」——三层 motivation 都写进 spec |
| 6 抽象层次恰当 | 4 | 大部分"做什么+关键参数",但要求 6/7 把 portfolio 配置和函数签名写得偏实现细节(等同 notebook 代码) |
| 7 正向指令为主 | 5 | 全部"做 X";要求 12「不要硬写'更高'或'更低'」是少数否定,但合理(要求动态描述) |
| 8 结构一致性 | 5 | 严格四段(上下文/任务/要求/结果呈现)+ 验证段,符合 q5 内部约定 |
| 9 简洁性 | 3 | 107 行,要求段 12 条,有些条目(要求 6 portfolio 配置常量、要求 7 函数签名)接近"代码翻译" |
| 10 学员可学习性 | 4 | 多个金融术语(夏普/卡玛/索提诺/Alpha)第一次集中出现,但都有一句话锚定 |
| 11 与 notebook 同步性 | 2 | indicators list vs dict 严重不一致;`stop_loss=0.05` 的写法 spec 与 notebook 一致但与 RP_PORTFOLIO 的"复用"定义有逻辑冲突(RP_SL_PORTFOLIO 与 RP_PORTFOLIO 实质是同一个 optimizer) |
| **合计** | **41/55** | 修改后可发布;维度 2、4、11 是修补重点 |

---

## 四、可改进点(带改写示例)

### 改进 1:锁死 end_date 与 oxq 版本【可复现】

**现状**(要求 4):
```
- 数据起始日期 START = "2021-01-01"
```

**改写**:
```
- 数据起始日期 START = "2021-01-01"
- 数据结束日期 END = "2026-03-18"  # 本章固定数据快照,所有图表数字以此为基准
- 库版本:open-xquant >= 0.4.0(本章功能在该版本可用)
```

**为什么**:notebook 实际用 `today = pd.Timestamp.now()`,意味着 2026 年和 2030 年学员跑出来的图表完全不同——这是全书最严重的【可复现】反模式之一。

### 改进 2:在 spec 中锁定指标的计算口径【精确】

**现状**(要求 2):只列出接口名 `result.sharpe_ratio()` + 一句话「夏普比(年化收益 / 波动率)」

**改写**:
```
2. 阅读 oxq 模块源码,确认指标的计算口径(锁定本章所有数字以此为准):
   - 年化方法:252 个交易日(非 365 自然日)
   - 夏普比:annualized_return / annualized_volatility,无风险利率视为 0
   - 卡玛比:annualized_return / abs(max_drawdown)
   - 索提诺比:annualized_return / downside_volatility(下行 = 收益 < 0 的标准差)
   - 基准的夏普比要用相同口径计算(252 + rf=0)
```

**为什么**:这些选择不是"实现细节",而是 q5 整章数字的**底层约定**。学员复制 spec 给不同 AI 跑,如果有的用 365、有的用 252,得出的 sharpe 数字不同,但学员看不出问题在哪。

### 改进 3:把 indicators 数据结构与 notebook 对齐【同步】

**现状**(要求 7):
```
- indicators 是指标列表(如 [RollingVolatility(period=20)])
```

**实际 notebook**:
```python
RP_IND = {"vol": (RollingVolatility(), {"column": "close", "period": 20})}
TNR_IND = {
    "vol": (RollingVolatility(), {"column": "close", "period": 20}),
    "mom": (Momentum(), {"column": "close", "period": 20}),
    ...
}
```

**改写**:
```
7. 定义辅助函数 run_strategy(portfolio, indicators=None, freq=10, stop_loss=None):
   - indicators 是 dict 形式 {"列名": (Indicator(), {"参数": 值})},
     例如 {"vol": (RollingVolatility(), {"column": "close", "period": 20})}
   - indicators 为 None 时表示无需指标(EqualWeight)
```

**为什么**:这是 spec 与 notebook 字符级不一致的最严重处。学员复制 spec,AI 按 list 写,运行报错,学员无法定位是 spec 错还是 AI 错。

### 改进 4:补机械可验证 assert【验证】

**现状**(验证段):描述性"5 行、8 列、有正有负"

**改写**:
```
执行成功的标志:
- 新增的单元格无报错运行完毕
- assert len(results) == 4, "应有 4 个策略结果"
- assert -0.5 < bh_max_dd < 0, f"基准最大回撤应为负且不超过 -50%,实际 {bh_max_dd:.2%}"
- assert all(0.3 < r.sharpe_ratio() < 3.0 for r in results.values()), \
    "策略夏普比应在合理范围 [0.3, 3.0]"
- 净值曲线图显示 5 条线(4 实线 + 1 虚线)
- 超额收益至少有一个为正
```

**为什么**:把"凭感觉判断"换成"机械可检"——失败立刻定位是数据问题还是计算问题。

### 改进 5:消除 RP 和 RP_SL 的"看似两个其实一个"模糊【精确】

**现状**(要求 6):
```
- RP_PORTFOLIO = RiskParityOptimizer(volatility_col="vol")
- RP_SL_PORTFOLIO = RiskParityOptimizer(volatility_col="vol")  # 与 RP 相同,止损在运行时指定
```

**改写**:删掉 RP_SL_PORTFOLIO 这条,改为在要求 8:
```
8. 运行四个策略(注意:RP+止损 复用 RP_PORTFOLIO,止损通过 stop_loss 参数传入,不需要单独建 optimizer):
   - RiskParity:run_strategy(RP_PORTFOLIO, ...)
   - RP+止损 5%:run_strategy(RP_PORTFOLIO, ..., stop_loss=0.05)
```

**为什么**:现状的 RP_SL_PORTFOLIO 是"形式上的复制"——同一个对象起两个名字,误导学员以为它们是不同 optimizer。删掉等价不冗余。

---

## 五、可沉淀的方法点

### A. 这份 spec 已经示范的原则

- **【动机】把"为什么用这把尺子"写进 spec**:要求 12 列三把尺子各自的关注点(夏普看总波动/卡玛看回撤/索提诺看下行)——可作为"金融指标教学不能止步于公式"的示范
- **【教学场景:open-xquant 框架】先读后写双层指示**:要求 2 读 RunResult,要求 5 读 portfolio optimizers——分别针对评估接口和构造参数,可作为"oxq 集成 spec 的标准开头"
- **【动机】用 Q0 概念呼应当前实验**:要求 10/12 两次主动呼应"还记得 Q0 说的 Alpha 吗"——可作为"跨章呼应让概念长在脑子里"的示范
- **【结构】把基准与策略放进同一张表**:要求 10 的「最后一行是基准」是这份 spec 最有教学价值的设计点——视觉上的"参照物"建立了对比锚
- **【正向】「根据实际数据动态描述方向,不要硬写'更高'或'更低'」**:要求 12 的这一句,把 LLM 的"看似中立其实瞎写"问题封死,可作为"防 LLM 幻觉"标准句

### B. 这份 spec 修补后可示范的原则

- **【可复现】数据快照锁 + 库版本锁**:当前 spec 没锁 end_date,notebook 用 `today` 动态取——修复后可作为"任何'最近 N 年'都是反模式"的原型 before/after
- **【精确】指标的计算口径必须显式**:当前只给中文名+一句话,没有 252/rf=0/下行口径——修复后可作为"金融指标 spec 的精度模板"
- **【同步】数据结构(list vs dict)是最隐蔽的漂移**:当前 spec 写 list、notebook 用 dict——修复后可作为"spec 涉及函数签名时必须给 minimal example"的示范
- **【验证】机械 assert 比"5 行 8 列"更强**:当前验证段只描述形状——修复后可作为"validation oracle 必须包含值域断言"的示范

### C. 领域/教学场景特殊考量

- **【教学场景】量化指标的"年化方法"是文化默契,但 spec 必须写明**:专业人士默认 252 + rf=0,但零基础学员不知道;同一个数字在不同文献里口径不同。q5 必须把这层默契显式化,否则学员无法跨数据源/跨工具对账
- **【教学场景:0 基础】基准的"等权买入持有"是 q5 教学的隐式锚**:不是套用 SPY/CSI300 这种现成基准,而是用学员自己的 ETF 池构造"什么都不做"基准——这个选择本身值得在方法点章节单列,因为它降低了"和大盘比"的概念门槛(SPY 是什么?CSI300 是什么?学员说不清,但"我手里这三只 ETF 等权躺平"他能想象)
- **【教学场景】oxq 框架的双重读源码**:既读 RunResult(产出端)也读 optimizers(输入端)——这是"既读输出契约也读输入契约"的标准实践,与通用 prompt 工程的"只描述需求不读源码"形成对照
