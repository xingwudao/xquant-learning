# spec：从因子到策略——让数据说话

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

`q9-daily-work.ipynb` 中已有 25 只 ETF 的动量因子 IC 分析结果，包括分组 IC 分析结果。可复用变量 `all_data`、`vol_df`、`fwd_dfs`、`ic_results`、`downloader` 和函数 `compute_ic_series`。`OxqMomentum`、`OxqRollingVol` 等尚未导入。当前需要扩展因子比较，并把研究发现转化为可检验的策略改进。

## 任务目标

比较更多因子的预测能力，并通过对照回测检验加入波动率过滤机制能否改善基础配置的表现。

## 执行要求

1. 创建第 3 步标题 Markdown（“从因子到策略——让数据说话”）。

2. 创建代码单元格：补充因子 IC 计算。
   - **波动率因子**：复用 spec 02 中的 `vol_df`
   - **短期反转因子**：对每只 ETF 分别用 `-df["close"].pct_change(5)` 计算近 5 日收益率的相反数，再合并成 `rev_df` 矩阵
   - 用 `compute_ic_series` 计算波动率因子和反转因子的 IC（20 日前向窗口）
   - 复用 spec 02 中风险调整动量的 IC 时间序列：`ic_results["风险调整动量 → 20日"]`
   - 打印 3 因子 IC 对比表（因子、IC 均值、IC 标准差、ICIR、IC 正值占比）

3. 创建因子评估发现 Markdown（“因子评估的发现”）：
   - 3 个因子各有侧重：风险调整动量兼顾价格趋势和波动大小，波动率看风险，短期反转看近期下跌后是否出现修复
   - 回顾 spec 02 的分组 IC 分析结果：在当前样本中，2 个动量因子在高波动组的 IC 均值均为负，且均低于低波动组的相应均值。未做显著性检验，分组 IC 分析结果只是后续假设的依据，不是这 2 个动量因子“失效”的证明
   - 因子较多时可以研究机器学习组合方法（决策树/随机森林、XGBoost/LightGBM、神经网络），这是未来方向
   - 当前先用最简单的方式——基于发现给策略加上波动率过滤机制

4. 创建策略改进方向 Markdown（“因子评估的发现能改进策略吗？”）：
   - 回顾前几章的 3 步关系：第 2 章把 GDP 作为筛选指标，将中国和美国的股票市场确定为优先研究的股票市场；相关性检查支持把黄金 ETF 加入标的池；风险调整动量为 3 只 ETF 提供权重分配依据
   - 分组 IC 分析结果提示可以检验波动率过滤机制。分组 IC 分析先在每个交易日按波动率高低对投资对象分组，再比较高波动组和低波动组的 IC 均值。波动率过滤配置则根据 3 只 ETF 的 20 日滚动波动率平均值是否超过阈值，决定是否缩减非现金目标权重。这是受分组 IC 分析结果启发的候选假设，不保证改善

5. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.core.Engine`
   - `oxq.core.Strategy`
   - `oxq.indicators.Momentum`（与 spec 02 使用的是同一 open-xquant 指标类，这里用别名`OxqMomentum`导入）
   - `oxq.indicators.RollingVolatility`（与 spec 02 使用的是同一 open-xquant 指标类，这里用别名`OxqRollingVol`导入）
   - `oxq.indicators.Ratio`
   - `oxq.portfolio.optimizers.TopNRankingOptimizer`
   - `oxq.signals.Threshold`
   - `oxq.trade.SimBroker`
   - `oxq.universe.StaticUniverse`
   - `oxq.rules.RebalanceFrequencyRule`

6. 创建代码单元格：下载第 3 章的 3 只 ETF，并运行本实验的基础配置回测。
   - 从 open-xquant 导入：`Engine`, `Strategy`, `Momentum as OxqMomentum`, `RollingVolatility as OxqRollingVol`, `Ratio`, `TopNRankingOptimizer`, `Threshold`, `SimBroker`, `StaticUniverse`, `RebalanceFrequencyRule`, `LocalMarketDataProvider as OxqMarket`
   - 第 3 章使用的 3 只 ETF：510300.SS（沪深 300 ETF）、513100.SS（纳指 100 ETF）、518880.SS（黄金 ETF）
   - 固定回测区间：2021-01-01 至 2026-03-26
   - 固定预热起始日期：2020-06-01
   - 使用 `YFinanceDownloader()` 下载时，下载窗口为 2020-06-01 至 2026-03-27（yfinance end 为半开区间）
   - 不使用 `pd.Timestamp.now()`、`today` 或任何运行时日期
   - 打印每只投资对象在 2021-01-01 至 2026-03-26 的交易天数
   - 本实验的基础配置：
     - `StaticUniverse(symbols=q3_symbols, name="q3-macro-etf")`
     - 用 `Threshold` 信号判断收盘价是否大于 0，`required_indicators`包含`mom`（20 日）、`vol`（20 日）和`ram`（`Ratio`）
     - 采用动量排名权重分配方法计算目标权重：`TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
     - 每隔 21 个交易日再平衡一次：`RebalanceFrequencyRule(interval_days=21)`，`data_start=Q3_DATA_START`
   - 打印基础配置的累计收益率、年化波动率、最大回撤和简化夏普

7. 创建代码单元格：构建波动率过滤配置。
   - 先计算 3 只 ETF 的 20 日滚动波动率平均值：使用 `RollingVolatility` 根据每日对数收益率，按样本标准差（`ddof=1`）计算每只 ETF 未年化的 20 日滚动波动率，再对 3 只 ETF 同一天的数值取平均（从 2020-06-01 至 2026-03-26）
   - 实现 `VolFilteredOptimizer` 类，包装 `TopNRankingOptimizer`：
     - 接受 `base_optimizer`、`vol_threshold`、`market_vol` 参数
     - `optimize()` 方法：先调用基础权重分配器的 `optimize()` 方法取得目标权重，再从 `indicators` 中取得当前最新日期，并在预先传入的 `market_vol` 序列中查找该日的 20 日滚动波动率平均值。若该值高于 `vol_threshold` 指定的阈值，则将所有非 `CASH` 目标权重减半，多余部分分配给 `CASH`
     - 暴露 `name` 属性和 `required_indicators` 属性
   - 仅使用预热期内截至 2020-12-31 的滚动波动率平均值：取 `q3_market_vol.loc[Q3_DATA_START:"2020-12-31"].dropna()` 的中位数作为波动率阈值，整个回测期间保持不变。确认预热截止日期早于 `Q3_START`，且参与计算的指标值非空；不得用 2021 年及以后的数据重新计算阈值
   - 打印实际参与阈值计算的首末日期、交易日数和阈值；另统计回测区间 2021-01-01 至 2026-03-26 内，指标值超过阈值的交易日占该指标非缺失交易日的比例，并标明“回测区间内高波动交易日占比”。该比例按实际数据计算，不预设为一半
   - 说明取中位数作为阈值和非现金目标权重减半均为教学设置，不代表最优参数
   - 构建波动率过滤配置（信号设置与基础配置相同，将`optimizer`换为`VolFilteredOptimizer`）
   - 运行回测，打印结果

8. 创建代码单元格：2 种配置对比。
   - 打印指标对比表（配置、累计收益率、年化波动率、最大回撤、简化夏普）
   - 画净值曲线对比图（画布大小为 14 英寸×7 英寸）：
     - 基础配置的净值曲线使用蓝色实线 `#3498DB`，波动率过滤配置的净值曲线使用橙色虚线 `#E67E22`。
     - 2 条曲线均归一化到起点 100。
     - 横轴为“年份”，纵轴为“归一化净值（起点=100）”；保留起始值 100 处的灰色水平虚线。
     - 图例在对应配置名称后标注“简化夏普：数值”，按整个回测区间计算，保留小数点后 2 位。
     - Notebook 独立输出的标题为“基础配置与波动率过滤配置的归一化净值曲线”；成书图由图下编号图题说明，不重复保留图内总标题。
   - 打印分析：对比简化夏普和最大回撤。若最大回撤收窄，则计算其绝对值缩小的百分比

9. 创建小结 Markdown：
   - 形成标的池和分配权重的 3 步关系（GDP 筛选指标 → 相关性检查 → 风险调整动量）
   - 分组 IC 分析提供线索（在当前样本中，2 个动量因子在高波动组的 IC 均值均为负）
   - 用线索提出并检验候选改进。根据实际结果说明最大回撤和简化夏普怎样变化，不预设改善
   - 量化日常循环：找因子 → 评估 → 发现问题 → 改进策略
   - 未来方向：更多因子、机器学习组合

## 验收标准

- 所有单元格无报错运行完毕
- 3 因子 IC 对比表有 3 行，IC 在合理范围内。按实际数据计算和分析，不以固定数值作为验收条件
- 第 3 章的 3 只 ETF 的数据固定读取到 2026-03-26，且均有数百条以上记录
- 因子评估发现、策略改进方向、第 3 章使用的 3 只 ETF 的数据覆盖、波动率阈值与高波动交易日占比、对简化夏普和最大回撤变化的分析及小结均已输出
- 基础配置和波动率过滤配置均有有效回测结果（累计收益率、简化夏普等非 `NaN`）
- 阈值仅由回测开始前、截至 2020-12-31 的预热数据计算，并在整个回测期间固定；高波动交易日占比只统计回测区间，不把预热日期或指标缺失值计入分母
- 净值曲线图显示 2 条线：基础配置使用蓝色，波动率过滤配置使用橙色。
- 对比表清晰展示 2 种配置的差异，分析文字与实际指标方向一致
