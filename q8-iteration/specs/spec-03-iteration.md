# spec：怎样用对照实验检验改动是否有效？——假设驱动的对照实验

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

在 `q8-iteration.ipynb` 中已有：
- 监控仪表盘和恶化时段检测结果
- 模拟执行差异、市场状态和参数稳定性 3 类诊断结果
- 已定义的变量：`result_base`、`equity`、`daily_ret`、`detector`、`high_vol_mask`、`market_vol`、`SYMBOLS`、`NAMES`、`START`、`END`、`DATA_END`、`CN_MARKET_CALENDAR`、`market`、`make_strategy`、`make_rules`、`FEE_MODEL`、`BEST_FREQ`、`BEST_SL`

诊断结果表明，当前策略没有专门针对高波动状态的仓位调整规则。

## 任务目标

完成再平衡间隔与波动率过滤机制的 2 轮对照实验，并形成可追溯的迭代记录。

## 执行要求

1. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.core.strategy` – `Strategy` 的 `hypothesis: str` 和 `objectives: dict` 字段
   - `oxq.core.engine` – `Engine.run()` 方法（注意 `rules` 参数）
   - `oxq.portfolio.optimizers` – `RiskParityOptimizer`
   - `oxq.observe` – `ExperimentLog`（`add()` 方法、`to_dataframe()` 方法）

2. 迭代 1——再平衡间隔对照实验：
   - 将基础配置的最大回撤减去 0.02，得到回撤下限 `dd_limit`，用于检查最大回撤是否比基础配置加深了超过 2 个百分点。
   - 先将以下假设写入 `Strategy` 的 `hypothesis` 字段：“缩短再平衡间隔，能让策略在高波动时段取得本次比较中最高的简化夏普。”同时填写对应的 `objectives`，明确判断条件：高波动时段简化夏普最高的配置所采用的再平衡间隔少于 21 个交易日，且相应配置的最大回撤比基础配置最多加深 2 个百分点。将条件记录为 `objectives={"best_high_vol_freq": {"target": "<21_days"}, "max_drawdown": {"limit": dd_limit}}`。
   - 打印策略的 `hypothesis` 和 `objectives` 字段值
   - 对 5、10、15、21、42 和 63 个交易日这 6 种再平衡间隔分别跑回测，`Engine.run()` 传入 `rules=make_rules(freq=间隔)`
   - 每次 `FillPriceMode.NEXT_OPEN` 回测都必须传入 `market_calendar=CN_MARKET_CALENDAR`
   - 全部回测使用 `start=START`、`end=DATA_END`
   - 用 `high_vol_mask` 找出高波动交易日，使用这些日期的日收益率计算各配置在高波动时段的简化夏普。
   - 打印指标对比表，列名依次为：再平衡间隔、全时段年化收益率、全时段最大回撤、全时段简化夏普、高波动时段简化夏普，21 个交易日一行标注“基础配置”
   - 在一张大小为 14 英寸×7 英寸的画布中绘制 6 条归一化净值曲线，分别对应 5、10、15、21、42 和 63 个交易日的再平衡间隔。其中 21 个交易日的基础配置曲线加粗，并用不同线型辅助区分各曲线。图例标题为“再平衡间隔（交易日）”，各项写成“间隔（高波动时段简化夏普）”，如“5（0.34）”。图注说明括号内的指标仅对应高波动时段，曲线则对应整个回测区间。
   - 先提示读者看最后一列高波动时段简化夏普，而不是倒数第 2 列全时段简化夏普。找出高波动时段简化夏普最高的配置，检查它是否同时满足前面 2 个判断条件。都满足时，判断假设获得支持，否则判断假设未获得支持。即使假设未获得支持，也要如实说明哪些短间隔配置的高波动时段简化夏普高于 21 个交易日基础配置的高波动时段简化夏普。
   - 保留 `iter1_results` 变量

3. 迭代 2——波动率过滤对照实验：
   - 先将以下假设写入 `Strategy` 的 `hypothesis` 字段：“市场年化波动率超过设定阈值时，降低持仓比例能显著收窄最大回撤。”在运行前把判断标准写入 `Strategy` 的 `objectives` 字段：与无过滤配置相比，最大回撤的绝对值至少缩小 30%，且简化夏普不低于 1.0。将条件记录为 `objectives={"max_drawdown_improvement": {"target": 0.30, "direction": "above"}, "sharpe_ratio": {"min": 1.0}}`。
   - 打印策略的 `hypothesis` 和 `objectives` 字段值
   - 先在当前 Notebook 中定义包装器 `VolFilteredOptimizer`，让它接收 `RiskParityOptimizer` 算出的目标权重，再根据市场年化波动率调整这些权重。这是本实验自行编写的代码，不是 open-xquant 内置类。
   - 本地包装器接收 `base_optimizer`、`vol_threshold` 和 `market_vol`。调用基础优化器得到权重后，如果最新日期的市场年化波动率高于 `vol_threshold` 指定的阈值，就把所有非 `CASH` 目标权重减半（乘以 0.5），相应增加 `CASH` 的目标权重；未超过阈值时，保持原权重。
   - 市场年化波动率使用 `detector.market_vol`（复用 spec 02 中的 `MarketStateDetector`）。该指标先根据每只 ETF 的每日简单收益率计算 20 日滚动样本标准差并年化，再对 3 只 ETF 取平均
   - 测试 4 种配置：无过滤配置（对照，使用 `RiskParityOptimizer`），以及市场年化波动率阈值为 10%、15% 和 20% 的配置（后 3 种使用 `VolFilteredOptimizer`）
   - `Engine.run()` 传入 `rules=make_rules()`
   - `FillPriceMode.NEXT_OPEN` broker 必须传入 `market_calendar=CN_MARKET_CALENDAR`
   - 回测窗口使用 `start=START`、`end=DATA_END`
   - 打印指标表：配置、年化收益率、最大回撤、简化夏普、最大回撤绝对值缩小比例。配置名称统一为“无过滤（对照）”“波动率过滤（阈值：10%）”“波动率过滤（阈值：15%）”“波动率过滤（阈值：20%）”。这里的阈值指市场年化波动率的触发值，超过该值时，将各 ETF 的目标权重减半，相应增加现金目标权重。
   - 在一张大小为 14 英寸×7 英寸的画布中绘制 4 条归一化净值曲线，分别对应无过滤以及市场年化波动率阈值为 10%、15% 和 20% 的配置。无过滤曲线加粗，用不同线型辅助区分各曲线。图例只列配置名称并保留对应线型，配置名称与指标表一致。曲线展示整个回测区间的归一化净值变化。
   - 2 张图的横轴均标为“年份”，纵轴均标为“归一化净值（起点=100）”，保留归一化起始值 100 的水平虚线。成书图删除与编号图题重复的图内标题，Notebook 独立输出保留必要标题。
   - 判断假设是否获得支持：逐一列出满足 2 个判断标准的配置；至少 1 个配置通过时，说明本轮过滤机制在当前样本和事前标准下获得支持；没有配置通过时，说明假设未获得支持
   - 如果仍保留 `best_label`，必须明确它按“最大回撤的绝对值缩小最多”选取，不得把它写成没有说明选择标准的唯一最佳配置
   - 打印取舍分析：分别说明通过配置的年化收益率、最大回撤的绝对值缩小幅度和简化夏普差异。2 个年化收益率相减时用百分点表示
   - 保留 `iter2_results`、`best_label`、`best_improve`、`best_freq_hv`、`best_hv_sharpe`、`dd_limit` 变量

4. 迭代记录表：
   - 用 `ExperimentLog(name="第 8 章迭代实验")` 创建记录
   - 用 `log.add()` 为每轮实验添加一条记录，填写实验名称 `name`、观察 `observation`、假设 `hypothesis`、判断标准 `criteria`、结果 `result`、结论 `conclusion` 和备注 `notes`。
   - 用 `log.to_dataframe().to_string(index=False)` 打印记录表
   - 打印过渡：这张表记录了每轮迭代的依据、过程和结论

## 验收标准

执行成功的标志：
- 单元格无报错运行完毕
- 迭代 1：6 种再平衡间隔的指标表完整，净值曲线图已保存，对假设的判断与实际结果一致
- 迭代 2：4 种配置指标表完整，净值曲线图已保存，对假设的判断与实际结果一致
- 迭代记录表包含 2 行，每轮 `conclusion` 与实际结果一致
- `Strategy` 的 `hypothesis` 和 `objectives` 字段值在输出中可见
