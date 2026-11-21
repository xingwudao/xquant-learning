# spec：从直觉到因子——回顾、评估方法与 GDP 因子实验

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

前面的实验已经使用过 GDP、动量等指标，但尚未把它们放入统一的因子研究框架。`q9-daily-work.ipynb` 中尚未建立因子评估实验。

## 任务目标

建立后续实验统一使用的 IC 评估方法，并用这一方法分别检验 GDP 总量排名和 GDP 增速排名与下一年 ETF 收益率排名之间的关系。本实验的 GDP 增速指按现价美元计算的 GDP 相对于上一年的变化率。这是使用当前可得数据的历史关系演示，不是还原当时可执行预测的实验。

## 执行要求

1. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.data.factors.WorldBankFetcher`
   - `oxq.data.factors.FactorDownloader`
   - `oxq.data.factors.read_factor`
   - `oxq.data.loaders.YFinanceDownloader`
   - `oxq.data.market.LocalMarketDataProvider`
   - `oxq.indicators.momentum.Momentum`
   - `oxq.indicators.rolling_volatility.RollingVolatility`

2. 创建章节标题 Markdown 单元格（“量化的日常是什么？”），说明前 8 章从零搭建了完整策略，这一章回头看这些决策背后的核心工作——因子研究。

3. 创建第 1 步标题 Markdown（“从直觉到因子”），包含因子回顾表，列名为“章节”“决策”“使用的指标”“本章中的因子类别”：
   - 第 2 章：确定优先研究哪些国家的股票市场；使用的指标为 GDP；本章中的因子类别为宏观因子。
   - 第 3 章：风险调整动量不为正的 ETF 权重设为 0，其余 ETF 按正值大小分配权重；使用的指标为风险调整动量；本章中的因子类别为动量因子。

4. 创建 IC 方法说明 Markdown：首次写明“信息系数（information coefficient，IC）”，后文使用 IC，说明它用于评估因子与后续收益率之间的相关性，本章采用斯皮尔曼相关系数计算 IC，比较因子值排名与随后指定时段的 ETF 收益率排名。解释 IC 均值绝对值的教学参考线（0.03、0.05 和 0.1），这些数值不是适用于所有市场和样本的统一标准。
   - 介绍 IC 信息比率（IC information ratio，ICIR）时，先说明它用于观察因子与后续收益率之间的关系在各期是否稳定，既考虑 IC 的平均水平，也考虑各期 IC 的波动。
   - IC 标准差大于 0 时，计算公式为：**ICIR=IC 均值÷IC 标准差**。
   - 说明正负关系：IC 均值为正时，ICIR 为正；IC 均值为负时，ICIR 为负。不将负值直接解释为因子没有研究价值。

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
   - 固定 GDP 年份窗口：2010—2024 年
   - 使用 `WorldBankFetcher()` + `FactorDownloader(fetcher, sub="macro")`
   - 调用 `dl.download("gdp", start=str(GDP_START_YEAR), end=str(GDP_END_YEAR), countries=countries)`
   - 用 `read_factor("gdp", ...)` 读取，打印形状
   - 以万亿美元为单位显示（除以 1e12），设置 columns.name="国家"、index.name="年份"

7. 创建代码单元格：下载作为 10 个国家市场代理的 ETF 价格数据。
   - 映射关系：USA→QQQ, CHN→FXI, JPN→EWJ, DEU→EWG, GBR→EWU, FRA→EWQ, IND→INDA, BRA→EWZ, CAN→EWC, KOR→EWY
   - 固定分析窗口：2011-01-01 至 2026-03-26
   - 使用 `YFinanceDownloader()` 下载，下载 end 用 2026-03-27（yfinance end 为半开区间）
   - 使用 `LocalMarketDataProvider().get_bars()` 读取到 2026-03-26
   - 打印 10 个国家对应的 ETF 行情数据覆盖表（国家、ETF、数据条数、起始/结束日期）

8. 创建代码单元格：计算 2 个 GDP 因子的年度 IC 并画图。
   - **GDP 总量因子**：比较当年 GDP 排名与下一年 ETF 收益率排名
   - **GDP 增速因子**：比较当年 GDP 增速排名（`gdp_df.pct_change()`）与下一年 ETF 收益率排名
   - ETF 年度收益率：年末收盘价/年初收盘价−1
   - IC 计算：对每个“因子所属年份→收益率所属年份”的配对，用 `scipy.stats.spearmanr` 计算相关系数
   - 在一张大小为 14 英寸×5 英寸的画布中，并排绘制 GDP 总量因子和 GDP 增速因子的年度 IC 柱状图。IC 为正时使用蓝色柱，为负时使用红色柱，并在每个子图中用蓝色虚线标出该因子的 IC 均值。
   - 打印 2 个 GDP 因子的 IC 均值和 ICIR

9. 创建代码单元格：GDP 总量排名与下一年 ETF 收益率排名的连线图（slope chart）。
   - 选 GDP 总量因子 IC 最大的那一年
   - 在一张大小为 8 英寸×6 英寸的画布中绘制因子排名与收益率排名的连线图。
   - 中国和美国使用红色粗线突出显示，其他经济体使用灰色细线。
   - 左侧标注 GDP 排名，右侧标注收益率排名
   - 中文国名映射

10. 创建 GDP 因子分析 Markdown：根据实际结果报告 GDP 总量因子和 GDP 增速因子的 IC 均值与 ICIR，并与本章教学参考线比较。说明年度配对和国家数量有限，不能仅凭当前结果证明第 2 章的选择正确。比较 2 个 GDP 因子的实际方向和强弱，不预设哪一个更优。

    结合本实验说明样本局限：仅使用 10 个国家十几年的年度数据，个别国家或年份的特殊表现就可能明显影响 IC 的估计结果。用 IC 观察因子值排名靠前的投资对象，其后续收益率排名倾向于靠前还是靠后，以及这种倾向是否明显；比较各年的 IC，再观察这种关系是否稳定。

    同时说明：当前下载没有还原各期 GDP 数据当时的发布日期及后续修订版本，本实验是历史关系演示，用于学习 IC 的计算和解读，不能据此认定这些 GDP 数值在当时已经可用于预测下一年的收益率。

11. 创建因子分类全景表 Markdown，包含 6 类因子：
    - 价值因子、动量因子、质量因子、波动率因子、宏观因子、另类因子。
    - 列名依次为“因子类别”“主要关注什么”“常见示例”“数据来源”，用通俗语言说明每类因子主要关注什么。
    - 另类因子的“主要关注什么”写“从新闻、卫星图像等数据中提取的量化线索”，“常见示例”写“新闻情绪指标”，“数据来源”写“新闻文本、卫星图像等”，不把卫星图像本身列为因子。
    - 表后简要说明另类因子是从非传统数据中提取的可计算特征，并以将新闻内容中偏乐观或偏悲观的倾向转化为新闻情绪指标为例。

12. 创建过渡 Markdown：GDP 因子受限于年度频率和小样本，接下来用日频价格数据和更多投资对象评估动量因子。

## 验收标准

- 所有单元格无报错运行完毕
- GDP 结果解释为历史排名关系，不将当前修订数据的 IC 等同于当时可执行的预测能力
- GDP 数据包含 10 个国家、2010—2024 年
- 10 只 ETF 数据固定读取到 2026-03-26，且均有数百至数千条记录
- GDP 数据表、10 个国家对应的 ETF 行情数据覆盖表、1×2 IC 柱状图、IC 均值和 ICIR、排名连线图、2 个 GDP 因子的分析结果、涵盖 6 类因子的分类全景表及过渡文案均已生成
- IC 柱状图包含当前数据窗口内所有可用的年度配对。若配对缺失，输出明确说明缺失年份和原因
- 排名连线图中，中国和美国使用红色粗线，其他经济体使用灰色细线，二者的视觉区分清楚可见。
- 按实际数据输出 GDP 因子的 IC、ICIR 及解读，不为贴合书中示例调整年份配对或计算方法。
