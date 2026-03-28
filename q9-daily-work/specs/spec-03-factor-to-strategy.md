# Spec: 从因子到策略——让数据说话

> 所有命令在沙箱外运行。

## 上下文

在 `q9-daily-work.ipynb` 的 Step 2 中，已完成 25 只标的的动量因子 IC 分析和分组分析。已有变量包括：`all_data`（25 只标的数据 dict）、`vol_df`（波动率矩阵）、`fwd_dfs`（前向收益 dict）、`ic_results`（6 组 IC 时间序列）、`compute_ic_series` 函数、`downloader`、`OxqMomentum`/`OxqRollingVol` 等尚未导入。本 spec 对应 Step 3（Cell 17-24），补充因子、总结发现、改进策略并回测对比。

## 任务

在 notebook 中新建 Step 3 的所有单元格：补充因子 IC、因子评估发现、策略改进框架、Q3 标的回测、波动率过滤改进、对比分析。

## 要求

1. 创建 Step 3 标题 markdown（"从因子到策略——让数据说话"）。

2. 创建代码单元格：补充因子 IC 计算。
   - **波动率因子**：复用 Step 2 中的 `vol_df`
   - **短期反转因子**：`-df["close"].pct_change(5)`（近 5 日收益取负），构建 `rev_df` 矩阵
   - 用 `compute_ic_series` 计算波动率因子和反转因子的 IC（20 日前向窗口）
   - 复用 Step 2 的 RAM IC：`ic_results["风险调整动量 → 20日"]`
   - 打印三因子 IC 对比表（因子、IC 均值、IC 标准差、ICIR、IC>0 占比）

3. 创建因子评估发现 markdown（"因子评估的发现"）：
   - 三个因子各有侧重：动量看趋势、波动率看风险、反转看短期超跌
   - 关键发现：动量因子在高波动标的上 IC 为负，波动率是动量失效的主要原因
   - 因子多了需要机器学习来组合（决策树/随机森林、XGBoost/LightGBM、神经网络），这是未来方向
   - 当前先用最简单的方式——基于发现给策略加波动率过滤

4. 创建策略改进方向 markdown（"因子评估的发现能改进策略吗？"）：
   - 两层选择框架：第一层 GDP 因子选候选池，第二层动量因子做择时
   - 因子评估告诉我们动量在高波动时容易出错，加波动率过滤应该能改善

5. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.core.Engine`
   - `oxq.core.Strategy`
   - `oxq.indicators.Momentum`（注意：oxq 内部的，非 Step 2 用的独立版本）
   - `oxq.indicators.RollingVolatility`（同上）
   - `oxq.indicators.Ratio`
   - `oxq.portfolio.optimizers.TopNRankingOptimizer`
   - `oxq.signals.Threshold`
   - `oxq.trade.SimBroker`
   - `oxq.universe.StaticUniverse`
   - `oxq.rules.RebalanceFrequencyRule`

6. 创建代码单元格：下载 Q3 三只标的并运行基准回测。
   - 导入 oxq 组件：`Engine`, `Strategy`, `Momentum as OxqMomentum`, `RollingVolatility as OxqRollingVol`, `Ratio`, `TopNRankingOptimizer`, `Threshold`, `SimBroker`, `StaticUniverse`, `RebalanceFrequencyRule`, `LocalMarketDataProvider as OxqMarket`
   - Q3 标的：510300.SS（沪深300）、513100.SS（纳指100）、518880.SS（黄金）
   - 起始日期 2021-01-01，结束日期用 `pd.Timestamp.now().strftime("%Y-%m-%d")`
   - 下载数据并打印每只标的的交易天数
   - 基准策略配置：
     - `StaticUniverse(symbols=q3_symbols, name="q3-macro-etf")`
     - `Threshold` 信号，required_indicators 包含 mom（20日）、vol（20日）、ram（Ratio）
     - `TopNRankingOptimizer(score_col="ram", n=3, filter_negative=True)`
     - `RebalanceFrequencyRule(interval_days=21)`，data_start="2020-06-01"
   - 打印基准策略的累计收益、年化波动率、最大回撤、夏普比率

7. 创建代码单元格：波动率过滤改进。
   - 先计算市场平均波动率：三只标的的 20 日波动率均值（从 2020-06-01 开始）
   - 实现 `VolFilteredOptimizer` 类，包装 `TopNRankingOptimizer`：
     - 接受 `base_optimizer`、`vol_threshold`、`market_vol` 参数
     - `optimize` 方法：先调用 base optimizer 获取权重，再从 indicators 中取最新日期查 market_vol，若超过阈值则将所有持仓权重减半、多余部分分配给 CASH
     - 暴露 `name` 属性和 `required_indicators` 属性
   - 波动率阈值取市场波动率的中位数，打印阈值和高波动天数占比
   - 构建波动率过滤策略（信号配置与基准相同，optimizer 换为 VolFilteredOptimizer）
   - 运行回测，打印结果

8. 创建代码单元格：两策略对比。
   - 打印指标对比表（策略、累计收益、年化波动率、最大回撤、夏普比率）
   - 画净值曲线对比图（figsize 14×7）：
     - 基准（蓝色 #3498DB）、波动率过滤（橙色 #E67E22）
     - 归一化到起点 = 100
     - 图例中标注各自夏普比率
     - 标题"因子评估 → 策略改进：基准 vs 波动率过滤"
   - 打印分析：对比夏普和回撤，若回撤改善则计算改善幅度

9. 创建小结 markdown：
   - 两层选择框架（GDP 因子 → 动量因子）
   - 因子评估发现问题（高波动时动量 IC 为负）
   - 用发现改进策略（波动率过滤降回撤）
   - 量化日常循环：找因子 → 评估 → 发现问题 → 改进策略
   - 未来方向：更多因子、机器学习组合

## 结果呈现

1. 三因子 IC 对比表
2. 因子评估发现 markdown
3. 策略改进方向 markdown
4. Q3 三只标的数据覆盖信息
5. 基准策略回测指标
6. 波动率阈值和高波动天数占比
7. 波动率过滤策略回测指标
8. 指标对比表
9. 净值曲线对比图
10. 动态分析文本
11. 小结 markdown

## 验证

- 所有单元格无报错运行完毕
- 三因子 IC 对比表有 3 行，IC 值在合理范围
- Q3 三只标的数据均有数百条以上记录
- 基准策略和波动率过滤策略均有有效回测结果（累计收益、夏普等非 NaN）
- 净值曲线图显示 2 条线（蓝色和橙色）
- 对比表清晰展示两种策略的差异
