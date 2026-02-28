# Spec: 用 GDP 数据锁定投资方向

> 所有命令在沙箱外运行。

## 上下文

在 `q2-what-to-buy.ipynb` 中已有：
- Step 1 的实验代码：个股 vs ETF 信号质量对比
- 学员已理解组合能对抗波动，选择用 ETF 而非个股

当前问题：全球 ETF 有几百只，怎么缩小范围？

## 任务

在 notebook 中新建代码单元格，展示全球主要经济体的 GDP 数据，用数据支撑"锁定中美"的选择，并获取对应 ETF 的历史价格数据。

## 要求

1. 在 notebook 中新建代码单元格
2. 使用 `WorldBankDownloader` 一次性下载全球前 10 大经济体的 GDP 数据：
   ```python
   from oxq.data import WorldBankDownloader, read_factor
   wb = WorldBankDownloader()
   countries = ["USA", "CHN", "DEU", "JPN", "IND", "GBR", "FRA", "ITA", "BRA", "CAN"]
   wb.download("gdp", countries=countries, start_year=2020, end_year=2024)
   ```
   注意：第一个参数是指标名 `"gdp"`，`countries` 是列表，一次调用下载所有国家。
3. 使用 `read_factor` 读取数据，取最新一年，转换为万亿美元：
   ```python
   gdp_raw = read_factor("gdp", countries=countries, start_year=2020, end_year=2024)
   latest_year = gdp_raw.index.max()
   gdp_latest = gdp_raw.loc[latest_year] / 1e12
   ```
4. 画一张横向柱状图（figsize 10×6）：
   - 按 GDP 从高到低排列
   - 中国和美国的柱子用红色和蓝色高亮，其余灰色
   - 在柱子右侧标注具体数值
   - 标题「全球前 10 大经济体 GDP」
5. 打印分析说明：中美两国 GDP 远超其他国家，合计占全球 GDP 的约 40%
6. 使用 open-xquant 下载两个对应的 ETF 最近 5 年数据（起始日期 `2021-01-01`，结束日期为当天）：
   - `YFinanceDownloader` 下载 `510300.SS`（沪深300ETF，代表中国核心资产）
   - `YFinanceDownloader` 下载 `QQQ`（纳斯达克100ETF，代表美国科技成长）
7. 使用 `LocalMarketDataProvider` 读取数据，画出两只 ETF 的归一化价格走势对比图（figsize 12×6）：
   - 将两只 ETF 的收盘价都归一化到起点 = 100
   - 两条线不同颜色，图例标注中文名称
   - 标题「沪深300 vs 纳斯达克100 归一化走势」

## 结果呈现

1. GDP 横向柱状图
2. 打印：「最直觉的思路：经济最强的国家，资本市场应该最有潜力。」
3. 打印：「数据说了算：锁定中国（沪深300 ETF）和美国（纳斯达克100 ETF）」
4. 两只 ETF 归一化走势对比图
5. 打印：「但一个新问题出现了——如果中美股市同时下跌怎么办？」
