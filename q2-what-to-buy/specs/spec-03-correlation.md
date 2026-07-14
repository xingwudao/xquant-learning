# Spec: 相关性分析与标的池构建

> 所有命令在沙箱外运行。

## 上下文

在 `q2-what-to-buy.ipynb` 中已有：
- 沪深300ETF（510300.SS）和纳指100ETF（513100.SS）的历史数据
- 学员已通过 GDP 数据锁定中美
- 当前问题：中美都是股市，可能同涨同跌，加什么能保护组合？

## 任务

在 notebook 中引入黄金 ETF 作为对冲资产，通过相关性分析验证三资产的分散化效果，并用 open-xquant 的 `StaticUniverse` 正式构建标的池。

## 固定实验日期

1. 三只 ETF 的价格窗口固定为：
   - `ETF_START = "2021-01-01"`
   - `ETF_END = "2026-03-03"`
2. 下载黄金 ETF 时使用 `ETF_DOWNLOAD_END = "2026-03-04"`。
3. `StaticUniverse.get_universe` 必须使用 `as_of_date=ETF_END`。
4. Notebook 不能使用 `today` 或当前日期计算价格窗口、标的池快照日期。

## 要求

1. 导入 `numpy`（年化波动率计算需要）。
2. 使用 `refresh_yfinance("518880.SS", start=ETF_START, end=ETF_DOWNLOAD_END)` 下载黄金ETF（518880.SS）的固定窗口数据。
3. 使用 `LocalMarketDataProvider().get_bars(symbol, start=ETF_START, end=ETF_END)` 读取三只 ETF 的数据：
   - `510300.SS`
   - `513100.SS`
   - `518880.SS`
4. 将三只 ETF 的收盘价合并为一个 DataFrame，列名改为中文：`{"510300.SS": "沪深300", "513100.SS": "纳指100", "518880.SS": "黄金"}`。
5. 计算日收益率（pct_change），然后计算相关性矩阵。
6. 画相关性热力图（figsize 8×6）：
   - 使用 matplotlib 的 `imshow`。
   - 在每个格子中标注相关系数数值（保留 2 位小数）。
   - 使用 `coolwarm` 色系。
   - 标题「三资产日收益率相关性」。
7. 对比实验——组合 vs 单押：
   - 单押方案：100% 沪深300。
   - 等权组合：沪深300、纳指100、黄金各 1/3。
   - 计算两种方案的日收益率序列。
   - 计算并对比：累计收益率、年化波动率、最大回撤。
8. 画两条累计收益率曲线对比图（figsize 12×6）：
   - 单押沪深300（灰色虚线）vs 等权三资产组合（实线）。
   - 图例标注方案名称。
   - 标题「单押沪深300 vs 三资产等权组合」。
9. 使用 open-xquant 构建标的池：
   ```python
   from oxq.universe import StaticUniverse
   universe = StaticUniverse(
       symbols=["510300.SS", "513100.SS", "518880.SS"],
       name="global-macro-etf"
   )
   snapshot = universe.get_universe(as_of_date=ETF_END)
   ```

## 结果呈现

1. 相关性热力图。
2. 打印相关性解读：
   - 「沪深300 与 纳指100 的相关性：X.XX —— 两个股票市场有一定联动，但并非完全同步」
   - 「沪深300 与 黄金 的相关性：X.XX —— 黄金与股市低相关，股市跌的时候它不一定跌」
   - 「纳指100 与 黄金 的相关性：X.XX」
3. 打印组合 vs 单押的对比表，使用 `metrics.to_string(index=False)`。
4. 固定窗口下的参考结果应四舍五入为：
   - 沪深300 与 纳指100 的相关性：`0.26`
   - 沪深300 与 黄金 的相关性：`0.09`
   - 纳指100 与 黄金 的相关性：`0.05`
   - 单押沪深300：累计收益率 `-1.78%`，年化波动率 `18.11%`，最大回撤 `-42.16%`
   - 三资产等权组合：累计收益率 `89.50%`，年化波动率 `12.36%`，最大回撤 `-16.49%`
5. 累计收益率对比图。
6. 打印关键认知：「数据说了算：分散风险的关键不是多买几个，而是买涨跌不同步的。」
7. 打印标的池构建结果：`「标的池构建完成: {snapshot.symbols}」`
