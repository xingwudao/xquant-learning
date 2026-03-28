# Spec: 动量因子 IC 分析——找到问题

> 所有命令在沙箱外运行。

## 上下文

在 `q9-daily-work.ipynb` 的 Step 1 中，已完成库导入、中文字体设置、GDP 因子 IC 实验。已有的变量包括：`downloader`（YFinanceDownloader）、`provider`（LocalMarketDataProvider）。本 spec 对应 Step 2（Cell 11-16），将标的池从 10 只扩展到 25 只，用日频数据做动量因子的 IC 分析。

## 任务

在 notebook 中新建 Step 2 的所有单元格：构建 25 只标的池、计算动量因子与前向收益、IC 分析表和图、按波动率分组的 IC 分析、问题总结。

## 要求

1. 创建 Step 2 标题 markdown（"动量因子——涨得好的会继续涨吗？"）。

2. 创建代码单元格：构建 25 只标的池并下载数据。
   - 22 个国家/地区 ETF + 3 个大宗商品 ETF，完整映射：
     - 原 10 国：USA→QQQ, CHN→FXI, JPN→EWJ, DEU→EWG, GBR→EWU, FRA→EWQ, IND→INDA, BRA→EWZ, CAN→EWC, KOR→EWY
     - 新增 12 国：AUS→EWA, TWN→EWT, MEX→EWW, ITA→EWI, ESP→EWP, SWE→EWD, NLD→EWN, THA→THD, MYS→EWM, ZAF→EZA, ISR→EIS, SGP→EWS
     - 大宗商品：GOLD→GLD, OIL→USO, SILVER→SLV
   - 时间范围：2015-01-01 至 2025-12-31
   - 复用 Step 1 的 `downloader` 和 `provider`
   - 打印覆盖表（代号、Ticker、中文名、起始/结束日期、交易天数）

3. 创建代码单元格：计算两个动量因子和三个前向收益窗口。
   - 使用 `Momentum().compute(df, column="close", period=20)` 计算 20 日动量
   - 使用 `RollingVolatility().compute(df, column="close", period=20)` 计算 20 日波动率
   - RAM = 动量 / 波动率（风险调整动量）
   - 前向收益窗口 [10, 20, 40] 交易日：`df["close"].pct_change(h).shift(-h)`
   - 构建横截面矩阵：`mom_df`, `ram_df`, `vol_df`, `fwd_dfs`（dict by horizon）
   - 打印矩阵形状和示例

4. 创建代码单元格：IC 分析，2 因子 × 3 窗口 = 6 组。
   - 实现 `compute_ic_series(factor_df, fwd_df, min_assets=5)` 函数：对每个交易日，取因子值和前向收益的交集标的（至少 min_assets 个），计算 Spearman IC
   - 打印 IC 对比表（因子→前向窗口、IC 均值、IC 标准差、ICIR、IC>0 占比）
   - 画 2×3 子图（figsize 18×8）：每格画 IC 柱状图（width=2, alpha=0.2, steelblue）+ 60 日滚动均值曲线（darkblue）+ IC 均值红色虚线
   - 总标题"两个动量因子 × 三个前向收益窗口 IC 对比"
   - 保留 `ic_ts = ic_results["风险调整动量 → 20日"]` 和 `fwd_df = fwd_dfs[20]` 供后续使用

5. 创建代码单元格：按标的自身波动率分组 IC 分析。
   - 实现 `compute_grouped_ic(factor_df, fwd_df, vol_df, min_assets=6)` 函数：
     - 每个交易日，取当天各标的的 20 日波动率，按中位数分为高波动组和低波动组
     - 分别在组内计算 Spearman IC
     - 要求交集标的至少 12 个，每组至少 min_assets 个
   - 对两个因子（20 日动量、风险调整动量）分别做分组 IC
   - 打印分组 IC 表（因子、整体 IC、高波动组 IC、低波动组 IC、Spread）
   - 以 RAM 为例画分组 IC 时间序列对比图（figsize 14×6）：
     - 高波动标的 IC（红色，60 日滚动均值）
     - 低波动标的 IC（蓝色，60 日滚动均值）
     - 图例中标注各组 IC 均值

6. 创建问题总结 markdown（"动量因子的问题"）：
   - 动量因子整体 IC 接近 0，截面预测能力很弱
   - 波动率是关键变量：高波动标的动量 IC 明显差于低波动标的
   - RAM 在低波动组表现更好，但对高波动标的依然无效
   - 结论：一个因子不够，需要补充能感知波动率环境的因子

## 结果呈现

1. 25 只标的覆盖表
2. 动量因子矩阵形状和示例数据
3. IC 对比表（6 组）
4. 2×3 IC 时间序列子图
5. 分组 IC 表
6. 分组 IC 时间序列对比图（高波动 vs 低波动）
7. 问题总结 markdown

## 验证

- 所有单元格无报错运行完毕
- 25 只标的全部加载成功
- IC 对比表有 6 行（2 因子 × 3 窗口），IC 均值绝对值在合理范围（接近 0）
- 2×3 子图中每格都有 IC 柱状图和滚动均值线
- 分组 IC 表显示高波动组 IC 低于低波动组（spread > 0）
- 分组 IC 对比图红蓝两条线走势有明显差异
