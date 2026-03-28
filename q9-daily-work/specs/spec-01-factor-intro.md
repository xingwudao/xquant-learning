# Spec: 从直觉到因子——回顾、评估方法与 GDP 因子实验

> 所有命令在沙箱外运行。

## 上下文

这是 Q9 章节的第一个 spec。学员已经完成 Q2-Q8，用 GDP 选国家、用动量排名买卖，但还不知道"因子"这个概念。本 spec 对应 notebook `q9-daily-work.ipynb` 的 Step 1（Cell 0-10），从零引入因子概念和 IC 评估方法，并用 GDP 数据做第一个因子评估实验。

## 任务

在 notebook `q9-daily-work.ipynb` 中创建 Step 1 的所有单元格：导入库、回顾因子表格、IC 方法说明、GDP 因子 IC 实验、排名对比图、GDP 分析、因子分类全景表。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.data.factors.WorldBankFetcher`
   - `oxq.data.factors.FactorDownloader`
   - `oxq.data.factors.read_factor`
   - `oxq.data.loaders.YFinanceDownloader`
   - `oxq.data.market.LocalMarketDataProvider`
   - `oxq.indicators.momentum.Momentum`
   - `oxq.indicators.rolling_volatility.RollingVolatility`

2. 创建章节标题 markdown 单元格（"量化的日常是什么？"），说明前八章从零搭建了完整策略，这一章回头看这些决策背后的核心工作——因子研究。

3. 创建 Step 1 标题 markdown（"从直觉到因子"），包含因子回顾表格：
   - Q2 选什么 → GDP 总量/增速 → GDP 因子 → 宏观因子
   - Q3 买多少 → 风险调整动量 → 动量因子 → 动量因子

4. 创建 IC 方法说明 markdown：解释 Spearman IC 的含义（因子排名 vs 收益排名的相似度）、IC 均值的参考阈值（0.03 / 0.05 / 0.1）、ICIR 的概念。

5. 创建代码单元格：导入库并设置中文字体。需要导入：
   - `warnings`（并 filterwarnings("ignore")）
   - `matplotlib.pyplot`, `numpy`, `pandas`, `scipy.stats`
   - `oxq.data.loaders.YFinanceDownloader`
   - `oxq.data.market.LocalMarketDataProvider`
   - `oxq.data.factors.WorldBankFetcher`, `FactorDownloader`, `read_factor`
   - `oxq.indicators.momentum.Momentum`
   - `oxq.indicators.rolling_volatility.RollingVolatility`
   - 设置 `plt.rcParams['font.sans-serif']` 和 `axes.unicode_minus`
   - 开启 `%matplotlib inline`

6. 创建代码单元格：下载 10 个国家的 GDP 数据。
   - 国家列表：USA, CHN, JPN, DEU, GBR, FRA, IND, BRA, CAN, KOR
   - 使用 `WorldBankFetcher()` + `FactorDownloader(fetcher, sub="macro")`
   - 调用 `dl.download("gdp", start="2010", end="2024", countries=countries)`
   - 用 `read_factor("gdp", ...)` 读取，打印形状
   - 以万亿美元为单位显示（除以 1e12），设置 columns.name="国家"、index.name="年份"

7. 创建代码单元格：下载 10 个国家对应 ETF 的价格数据。
   - 映射关系：USA→QQQ, CHN→FXI, JPN→EWJ, DEU→EWG, GBR→EWU, FRA→EWQ, IND→INDA, BRA→EWZ, CAN→EWC, KOR→EWY
   - 使用 `YFinanceDownloader()` 下载，时间范围 2011-01-01 至 2026-12-31
   - 使用 `LocalMarketDataProvider().get_bars()` 读取
   - 打印覆盖表（国家、ETF、数据条数、起始/结束日期）

8. 创建代码单元格：计算两个 GDP 因子的年度 IC 并画图。
   - **GDP 总量因子**：当年 GDP 排名 → 预测下一年 ETF 收益排名
   - **GDP 增速因子**：当年 GDP 增速排名（`gdp_df.pct_change()`）→ 预测下一年 ETF 收益排名
   - ETF 年度收益率：年末收盘价 / 年初收盘价 - 1
   - IC 计算：对每个"因子年→收益年"配对，用 `scipy.stats.spearmanr` 计算相关系数
   - 画 1×2 并排柱状图（figsize 14×5），正相关蓝色、负相关红色，加 IC 均值虚线
   - 打印两个因子的 IC 均值和 ICIR

9. 创建代码单元格：IC 排名对比图（slope chart）。
   - 选 GDP 总量因子 IC 最大的那一年
   - 画因子排名 vs 收益排名的连线图（figsize 8×6）
   - 中美两国用红色粗线高亮，其他灰色细线
   - 左侧标注 GDP 排名，右侧标注收益排名
   - 中文国名映射

10. 创建 GDP 因子分析 markdown：GDP 总量因子 IC 均值为正，呼应 Q2 选中美的逻辑；GDP 增速因子更差；局限性（年度数据、小样本）。

11. 创建因子分类全景表 markdown，6 类因子：
    - 价值、动量、质量、波动率、宏观、另类
    - 每类一句话含义、常见例子、数据来源

12. 创建过渡 markdown：GDP 因子受限于年度频率和小样本，接下来用日频价格数据和更多标的评估动量因子。

## 结果呈现

1. 库导入成功提示
2. GDP 数据表（万亿美元）
3. 10 国 ETF 覆盖表
4. 1×2 GDP 因子 IC 柱状图（总量 vs 增速）
5. IC 均值和 ICIR 打印
6. 排名对比 slope chart（最佳 IC 年份）
7. GDP 分析 markdown
8. 因子分类全景表
9. 过渡文案

## 验证

- 所有单元格无报错运行完毕
- GDP 数据包含 10 个国家、2010-2024 年
- 10 只 ETF 数据均有数百至数千条记录
- IC 柱状图显示约 10 个年度配对，正负均有
- slope chart 中美两国红色高亮可见
- 因子分类表有 6 行
