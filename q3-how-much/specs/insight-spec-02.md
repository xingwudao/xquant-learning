# Insight: spec-02-risk-parity — 风险平价：仓位分配的概念升级

> **评分 41/55** · 修改后可发布；维度 4「可复现性」与 9「简洁性」需修补
> 评审基线：q1/insight-spec-01 同款 11 维 spec rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标

---

## 一、设计意图复盘

这是 q3 三联 spec 的第二份，承担**概念升级**的角色——从"等权（什么都不看）"过渡到"风险平价（看波动率）"。spec 引入第一个量化概念：**波动率倒数加权**，是后续动量排名（更复杂的排序）的概念前置。spec 的简洁性体现在：只比 spec-01 多一个 `RiskParityOptimizer` 和波动率列设置，其他全部复用——这种"差量式 spec"是仓位分配三联 spec 的核心设计。【结构】【教学场景：渐进难度】

**为什么提取 COMMON 字典**：spec 第 4 条要求"提取 spec-01 中等权策略与风险平价策略的公共部分为 `COMMON` 字典，使两个策略只在 `portfolio` 优化器一行不同"。这条要求是 spec 写作的精彩示范：**让对比的差异点单点暴露**，学员一眼看到"等权 vs 风险平价的唯一区别就是 portfolio 这一行"。但 notebook 实际**没有真的提取 COMMON 字典**——两次 `Strategy(...)` 仍然完整写出 universe/signals/portfolio 三个参数，只在 portfolio 处变化。这是 spec 与 notebook 的实质性漂移。【同步】

**为什么用 RollingVolatility 而非 close.std()**：spec 通过 `signal_rp.required_indicators = {"vol": (RollingVolatility(), {"column": "close", "period": 20})}` 在 signal 上注册指标，让 oxq 内部自动计算。这种"在信号上声明依赖指标"是 oxq 框架的核心设计，spec 通过 required_indicators 这条具体语法把它教给 AI。【教学场景：oxq 框架】

**结果呈现的双图设计**：spec 既要净值曲线对比图（垂直对比），又要权重历史堆叠面积图（水平展示"权重如何随波动率调整"）。后者是仓位分配章的灵魂可视化——**让学员看到权重不是一成不变的**。这条堆叠面积图是 q3 三联 spec 中第一次出现，是仓位分配教学的关键可视化模板。【教学场景：仓位分配】

**末尾分析话术固化的张力**：spec 末尾两句分析（"组合波动率从 X 降到 Y" / "桥水基金的全天候策略"）默认了"风险平价确实降低了波动率"。验证段写了"风险平价组合年化波动率 ≤ 等权组合"作为机械断言——这点比 spec-01 进步：把"分析话术暗含的方向"转化成可验证条件。【验证】但 spec 没有 fallback：如果验证失败（极端市场风险平价反而波动更大），分析话术该怎么改？这条留白是反模式 14（无 fallback 的指令）。

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| 提取 `COMMON` 字典让两策略只差 portfolio 一行 | notebook 仍完整写两次 `Strategy(...)`，只是 portfolio 不同 | **实质性漂移**：spec 的精彩教学设计未在 notebook 落地，违反【同步】 |
| `RiskParityOptimizer` + `Threshold` 信号配 vol 列 | `RiskParityOptimizer(volatility_col="vol")` + `signal_rp.required_indicators` 显式设 vol | spec 写大意，notebook 给具体语法——同步但 spec 略抽象 |
| 「使用 spec-01 中已预计算的 vol 列」 | spec-01 没真预计算，spec-02 这里才注册 | spec-01 → spec-02 接续承诺断裂，已在 insight-spec-01 改进 4 中标注 |
| 权重对比表 + 10 万元换算 | 一致 | 同步 |
| 指标对比表（累计收益率/年化波动率/最大回撤） | 一致，且 notebook 多打印了等号分隔线和列宽控制 | 同步，notebook 更精细 |
| 净值曲线对比图 figsize 12×6，灰虚 + 蓝实 | 一致 | 同步 |
| 权重历史堆叠面积图 figsize 12×4 | 一致 | 同步 |
| 末尾分析「波动率从 X 降到 Y / 最大回撤从 X 收窄到 Y」 | f-string 动态填充 | 优秀，但「降到/收窄」方向词被硬写——若极端情况风险平价波动反升，话术会自相矛盾 |
| 验证段「风险平价权重三只 ETF 不相等」 | notebook 无 assert | 验证写在 spec 里却没机械断言 |
| 验证段「风险平价组合的年化波动率 ≤ 等权组合」 | notebook 无 assert | 同上，机械断言缺位 |

**对照结论**：spec 大方向同步，但 **COMMON 字典提取**这条精彩教学设计在 notebook 完全没落地——是 spec-02 最大的漂移。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | 「风险平价策略 + 与等权对比」紧耦合 |
| 2 可验证性 | 4 | 验证段有方向性断言（vol ≤ 等权 vol），但无机械 assert |
| 3 输出契约具体度 | 4 | figsize/标题/线型明确，缺权重数值精度（与 spec-01 同样问题） |
| 4 **可复现性** | **2** | **继承 spec-01 的"当天"问题**，未声明 oxq 版本 |
| 5 上下文 / 动机充分度 | 5 | 上下文承接 spec-01，"为什么需要风险平价"自然导出 |
| 6 抽象层次恰当 | 5 | 不规定 RiskParityOptimizer 内部算法，只给参数 |
| 7 正向指令为主 | 5 | 全部"做 X" |
| 8 结构一致性 | 5 | 严格四段 + 验证段 |
| 9 简洁性 | **3** | 56 行不算长，但「COMMON 字典」「使用 spec-01 已预计算」两条都没在 notebook 落地，等于无效要求 |
| 10 学员可学习性 | 4 | 概念清晰（波动率倒数加权），但 oxq 的 `required_indicators` 语法对 0 基础略陡 |
| 11 与 notebook 同步性 | **3** | COMMON 字典实质性漂移 + 「已预计算 vol」承诺断裂 |
| **合计** | **41/55** | 修改后可发布；维度 4、9、11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：COMMON 字典要么兑现要么删【同步】【简洁】

**现状**（spec 第 4 条）：
```
提取 spec-01 中等权策略与风险平价策略的公共部分为 COMMON 字典，使两个策略只在 portfolio 优化器一行不同（信号均使用 Threshold）。
```

但 notebook 没真这么做——两次 `Strategy(...)` 完整写出。spec 的"精彩教学设计"成了空头支票。

**改写**（兑现：spec 直接给 COMMON 字典代码，notebook 必须复用）：
```
4. 定义公共配置 COMMON（让等权与风险平价唯一差异为 portfolio 一行）：
   COMMON = dict(
       universe=universe,
       signals={"active": (signal, {"column": "close", "threshold": 0, "relationship": "gt"})},
   )
   等权策略：Strategy(name="equal-weight", **COMMON, portfolio=EqualWeightOptimizer())
   风险平价：Strategy(name="risk-parity", **COMMON_RP, portfolio=RiskParityOptimizer(volatility_col="vol"))
   注：风险平价的 signal 需要额外注册 vol 指标，所以信号实例不同——但参数结构一致。
```

或者直接删掉这条，让 spec 与 notebook 都接受"两次完整写"的事实。**写了就要兑现，不兑现就删**。

### 改进 2：继承 spec-01 的 end_date 修复【可复现】

风险平价 spec 复用 spec-01 的下载数据（spec-02 中没重新下载 step），所以 spec-01 的"当天"问题会传染。修复 spec-01 即可同时修复 spec-02——这就是 q3 三联 spec 链的级联。

### 改进 3：补权重和的机械 assert（与 spec-01 同款模板）【验证】【教学场景：仓位分配】

**现状**：spec-02 验证段「风险平价权重三只 ETF 不相等」「年化波动率 ≤ 等权组合」全是描述。

**改写**（加到结果呈现 第 0 条）：
```
0. 权重与指标合法性检查：
   rp_w = rp_weights_df.iloc[-1]
   assert abs(rp_w.sum() - 1.0) < 1e-6, f"风险平价权重和应为 1.0"
   assert rp_w.nunique() > 1, "风险平价权重不应全相等（否则退化为等权）"
   assert result_rp.annualized_volatility() <= result_ew.annualized_volatility() * 1.05, \
       "风险平价波动率显著高于等权，与设计预期不符——检查 vol 列计算"
```

第三条 assert 给出 5% 容忍度，避免极端日期下因数据噪音误报。

### 改进 4：分析话术给 fallback【正向】【验证】

**现状**（结果呈现 第 5 条）：
```
「波动大的少买点、波动小的多买点——组合波动率从 X.XX% 降到 X.XX%，最大回撤从 X.XX% 收窄到 X.XX%。」
```

**改写**（学习 spec-03 的动态描述方式）：
```
5. 打印分析（根据实际数据动态描述方向）：
   - 对比组合波动率与最大回撤的变化方向（若降则用"降到/收窄"，若升则说明可能是 vol 估计期偏短或数据异常）
   - 「这种方法叫风险平价（Risk Parity）...桥水基金...」
```

spec-03 已经做了"动态描述方向，不要硬写'更大'或'更深'"，spec-02 反而用了硬写——逆向不一致，应统一。

### 改进 5：「使用 spec-01 已预计算的 vol 列」承诺要清【同步】

**现状**（要求 第 2 条）：
```
用 RiskParityOptimizer 构建组合优化器，配合 Threshold 信号计算权重（使用 spec-01 中已预计算的 vol 列）...
```

但 spec-01 没真预计算（参见 insight-spec-01 改进 4）。spec-02 这条说"使用已预计算"是基于错误前提。

**改写**：
```
2. 用 RiskParityOptimizer 构建组合优化器，在 Threshold 信号上注册 vol 指标：
   signal_rp = Threshold()
   signal_rp.required_indicators = {
       "vol": (RollingVolatility(), {"column": "close", "period": 20}),
   }
   注：vol 在此处按需注册，非 spec-01 的预计算结果。
```

直接给注册语法，spec 与 notebook 字符级一致。

---

## 五、可沉淀的方法点（用于书中方法/模板章节）

> 标签体系（10 个）：【结构】【精确】【可复现】【动机】【验证】【正向】【简洁】【同步】【可学习】【教学场景】

### A. 这份 spec 已经示范的原则

- **【结构】差量式 spec**：spec-02 只比 spec-01 多 portfolio 一行不同，其他复用 — 仓位分配三联 spec 的核心设计，可作为「连续对比型 spec 链」方法素材
- **【教学场景：oxq 框架】signal.required_indicators 语法**：通过 `signal_rp.required_indicators = {"vol": (RollingVolatility(), {...})}` 教 AI 在信号上注册指标依赖 — 这是 oxq 的核心设计模式，spec 把它写成具体语法而非抽象描述，是「先读后写」的良好补充
- **【验证】方向性断言写进验证段**：「风险平价组合年化波动率 ≤ 等权组合」把"分析话术暗含的方向"转化成可验证条件 — 比单纯描述前进了半步
- **【教学场景：仓位分配】堆叠面积图模板首次出现**：权重历史堆叠面积图（figsize 12×4，alpha=0.8，y 轴 0-1）— 仓位分配章的灵魂可视化，可作为「权重变化可视化」固定模板

### B. 这份 spec 修补后可示范的原则

- **【同步】写了就要兑现，不兑现就删**：spec 第 4 条「提取 COMMON 字典」是精彩设计，但 notebook 没落地 — 修复后作为「spec 中的'抽取公共逻辑'必须给具体代码片段」的范例
- **【验证】仓位分配灵魂断言「权重和=1.0」（与 spec-01 同款）**：q3 三个 spec 都缺，三次缺位证据足够强 — 修复后作为「领域特殊验证模板必含」的标杆
- **【正向】分析话术动态描述方向**：spec-03 已做，spec-02 反而硬写 — 修复后作为「spec 内部一致性」的反模式（同章三 spec 应用同一模板）
- **【可复现】end_date 级联修复**：spec-02 的复现性问题来自 spec-01 — 修复后作为「连续 spec 链中复现性问题的级联性」范例

### C. 领域 / 教学场景特殊考量（不通用但必须教）

- **【教学场景：仓位分配】「差量式 spec」的简洁哲学**：当一组 spec 是"同一基础上的不同方法"时，spec 应让差异点**单点暴露**——COMMON 公共部分 + 唯一差异行。这是仓位分配章的特殊写法（不是所有章节都适用，只在"方法对比型"章节才显著）
- **【教学场景：oxq 框架】signal.required_indicators 是核心语法**：oxq 用这条语法把"信号需要哪些指标"声明在信号本身上，spec-02 是首次出现 — 后续 q4-q9 涉及更多指标时这条会反复用，应作为 oxq 核心模式之一在方法章节单列
- **【教学场景：仓位分配】权重历史堆叠面积图是教学灵魂**：等权下面积图三条带等宽，看不出动态；风险平价下面积带宽随时间变化，**让学员一眼看到"权重不是一成不变的"**。这条可视化是仓位分配章的核心，spec 必须包含
