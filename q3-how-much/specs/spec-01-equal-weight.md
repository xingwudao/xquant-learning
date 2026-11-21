# spec：各买 1/3——等权组合

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

当前标的池已经确定为沪深 300 ETF、纳指 100 ETF 和黄金 ETF，但尚未确定 3 只 ETF 的资金分配比例。本 spec 先采用等权分配方法（简称“等权”），也就是把资金按相同比例分给 3 只 ETF。

## 任务目标

运行等权组合回测，并将组合与 3 只 ETF 单独持有的表现放在一起比较。

## 执行要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.portfolio.optimizers.EqualWeightOptimizer`
   - `oxq.signals.Threshold`
   - `oxq.core.Engine`、`oxq.core.Strategy`
   - `oxq.rules.RebalanceFrequencyRule`
   - `oxq.trade.SimBroker`
   - `oxq.data.YFinanceDownloader`、`oxq.data.LocalMarketDataProvider`
   - `oxq.universe.StaticUniverse`

3. 创建 Notebook `q3-how-much.ipynb`，导入所需库并设置中文显示（macOS：Arial Unicode MS/STHeiti；Windows：SimHei；`axes.unicode_minus = True`，使坐标轴负值使用数学减号）。

4. 定义常量和标的中文名映射：
   ```python
   SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")
   SYMBOL_NAMES = {
       "510300.SS": "沪深 300 ETF",
       "513100.SS": "纳指 100 ETF",
       "518880.SS": "黄金 ETF",
   }
   START = "2021-01-01"
   END = "2026-03-18"
   ```

5. 使用 `YFinanceDownloader` 下载 3 只 ETF 的日线行情数据，数据窗口固定为 `2021-01-01` 到 `2026-03-18`。
   不要使用 `today`、`now()` 或默认截止到最新数据的下载方式。
   `yfinance` 的 `end` 参数是排他边界。代码中可用 `2026-03-19` 作为下载结束参数，再按 `END = "2026-03-18"` 读取。
   下载调用用 `refresh_yfinance(symbol, START, DOWNLOAD_END)` 包装。如果下载失败，打印错误并继续使用本地缓存。

6. 用 `StaticUniverse` 在代码中表示第 2 章已经形成的标的池：
   ```python
   universe = StaticUniverse(symbols=SYMBOLS, name="global-macro-etf")
   ```

7. 使用 `LocalMarketDataProvider` 加载数据。取 3 只 ETF 日期索引的交集，保存为共同交易日 `common_trading_days`，供本章后续绘图使用。绘图时将各条曲线和目标权重序列对齐到这组日期，不据此删改回测输入数据。

8. 用 `EqualWeightOptimizer` 实现等权。使用 `Threshold` 信号（`column="close", threshold=0, relationship="gt"`），打印最新一天每只 ETF 的目标权重。

9. 打印权重的具体含义——假如总资金为 10 万元，按权重换算每只的目标金额。末尾加一句解释：权重（weight）就是“这笔钱怎么分”——每只 ETF 分到总资金的百分之多少。目标金额不等于真实成交金额。目标权重和目标金额均保留 2 位小数，计算和检查仍使用未舍入值。

10. 对 3 只 ETF 分别计算**单独持有**的表现指标（累计收益率、年化波动率、最大回撤），用于与组合对照。单只 ETF 的年化波动率根据每日对数收益率按样本标准差（`ddof=1`）计算，再乘以 `√252`；组合使用 `result.annualized_volatility()`，计算方法相同。

11. 组装采用等权分配方法的策略并运行回测。策略参数：
    - 使用 `Threshold` 信号（`column="close", threshold=0, relationship="gt"`）检查收盘价是否大于 0。在本章正价格数据中，该条件始终成立
    - 权重分配方法使用 `EqualWeightOptimizer()`
    - 再平衡交易规则 `RebalanceFrequencyRule(interval_days=10)` 传入 `Engine.run(rules=[...])`
    - 目标权重时间序列通过 `result.weights_df()` 提取

12. 画净值曲线图（画布大小为 12 英寸×6 英寸）：
    - 沪深 300 ETF、纳指 100 ETF 和黄金 ETF 的单独持有曲线分别使用灰色虚线、灰色点线和灰色点划线。
    - 等权组合的净值曲线使用加粗的蓝色实线。
    - 全部归一化到起点=100。横轴标“年份”，纵轴标“归一化净值（起点=100）”；单只 ETF 的曲线以归一化收盘价表示单独持有表现，与组合净值分别标明
    - 标题“各买 1/3：等权组合 vs 单只持有”

### 结果呈现

1. 打印权重分配结果和 10 万元换算结果。

2. 打印对比表。

   | 比较对象 | 累计收益率 | 年化波动率 | 最大回撤 |
   |------|-----------|-----------|---------|
   | 沪深 300 ETF | *X.XX*% | *X.XX*% | *X.XX*% |
   | 纳指 100 ETF | *X.XX*% | *X.XX*% | *X.XX*% |
   | 黄金 ETF | *X.XX*% | *X.XX*% | *X.XX*% |
   | **等权组合** | ***X.XX*%** | ***X.XX*%** | ***X.XX*%** |

3. 绘制净值曲线对比图。

4. 打印分析：
   - “3 只 ETF 各自的年化波动率从 *X.XX*% 到 *X.XX*%，最高约为最低的 *N* 倍。”
   - “但等权分配方法的逻辑是：不管你多颠簸，都分到一样多的钱。在本章使用的 3 只 ETF 中，波动较大的 ETF 可能对组合涨跌产生更大影响。精确的风险贡献还取决于 ETF 之间的相关性。”
   - “有没有更聪明的分法——比如，波动大的少买点？”

5. 在对比表后打印波动率计算方法说明：单只 ETF 和组合均根据每日对数收益率计算年化波动率，并按 252 个交易日年化。

## 验收标准

使用 `START = "2021-01-01"`、`END = "2026-03-18"`，并采用本书配套代码所使用的 open-xquant 版本复现时，参考结果为：
- 沪深 300 ETF：累计收益率 `-2.11%`，年化波动率 `18.06%`，最大回撤 `-42.16%`
- 纳指 100 ETF：累计收益率 `106.44%`，年化波动率 `22.67%`，最大回撤 `-27.50%`
- 黄金 ETF：累计收益率 `171.81%`，年化波动率 `15.91%`，最大回撤 `-16.77%`
- 等权组合：累计收益率 `86.70%`，年化波动率 `12.50%`，最大回撤 `-16.47%`

### 其他验收标准

执行成功的标志：
- Notebook 中所有单元格无报错运行完毕
- 打印出 3 只 ETF 在等权下的目标权重（每只约 33.3%）和 10 万元换算
- 最新目标权重均非负，且权重和与 1.0 的差不超过 1×10⁻⁶
- 对比表包含 4 行（3 只 ETF + 等权组合），3 列指标均为有效数值（非 NaN、非无穷值）
- 净值曲线图显示 4 条线：3 只 ETF 的单独持有曲线均为灰色并使用不同线型，等权组合曲线为蓝色实线。
