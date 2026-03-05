# Spec: 等权组合——最简单的"各买多少"

> 所有命令在沙箱外运行。

## 上下文

本章探讨"买多少"。Q2 选好了 3 只 ETF（沪深300、纳指100、黄金），现在要回答：每只各买多少？

## 任务

在 notebook `q3-how-much.ipynb` 中创建代码，跑等权组合回测，并展示三只 ETF 各自的表现差异。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解各接口的输入、输出和参数含义：
   - `oxq.signals.EqualWeight`
   - `oxq.indicators.RollingVolatility`
   - `oxq.core.Engine`、`oxq.core.Strategy`
   - `oxq.rules.RebalanceRule`
   - `oxq.trade.SimBroker`
   - `oxq.data.YFinanceDownloader`、`oxq.data.LocalMarketDataProvider`
   - `oxq.universe.StaticUniverse`

3. 创建 notebook `q3-how-much.ipynb`，导入所需库并设置中文显示（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）。

4. 定义常量和标的中文名映射：
   ```python
   SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")
   SYMBOL_NAMES = {
       "510300.SS": "沪深300ETF",
       "513100.SS": "纳指100ETF",
       "518880.SS": "黄金ETF",
   }
   START = "2021-01-01"
   ```

5. 使用 `YFinanceDownloader` 下载 3 只 ETF 数据（起始日期 `2021-01-01`，结束日期为当天）。

6. 构建投资宇宙：
   ```python
   universe = StaticUniverse(symbols=SYMBOLS, name="global-macro-etf")
   ```

7. 使用 `LocalMarketDataProvider` 加载数据，并为每只 ETF 预计算 20 日滚动波动率（后面 spec-02 会用到）。

8. 用 `EqualWeight` 信号计算权重，打印最新一天每只 ETF 的权重值。

9. 打印权重的具体含义——假如总资金 10 万元，按权重换算每只各买多少钱。末尾加一句解释：权重（Weight）就是"这笔钱怎么分"——每只标的分到总资金的百分之多少。

10. 对三只 ETF 分别计算**单独持有**的表现指标（累计收益率、年化波动率、最大回撤），用于与组合对比。

11. 组装等权策略并运行回测。策略参数：
    - 信号列名 `"tw"`
    - 指标包含 20 日滚动波动率
    - 再平衡频率 10 个交易日

12. 画净值曲线图（figsize 12×6）：
    - 三只 ETF 单独持有的净值线（灰色，用不同线型区分：虚线、点线、点划线）
    - 等权组合的净值线（蓝色实线，加粗）
    - 全部归一化到起点 = 100
    - 标题「各买三分之一：等权组合 vs 单只持有」

## 结果呈现

1. 打印权重分配 + 10 万元换算

2. 打印对比表：

   | 标的 | 累计收益率 | 年化波动率 | 最大回撤 |
   |------|-----------|-----------|---------|
   | 沪深300 ETF | X.XX% | X.XX% | X.XX% |
   | 纳指100 ETF | X.XX% | X.XX% | X.XX% |
   | 黄金 ETF | X.XX% | X.XX% | X.XX% |
   | **等权组合** | **X.XX%** | **X.XX%** | **X.XX%** |

3. 净值曲线对比图

4. 打印分析：
   - 「三只 ETF 各自的年化波动率从 X.XX% 到 X.XX%，差了 N 倍。」
   - 「但等权信号说：不管你多颠簸，都买一样多的钱。波动最大的那只，虽然只花了 1/3 的钱，却主导了组合的涨跌。」
   - 「有没有更聪明的分法——比如，波动大的少买点？」

## 验证

执行成功的标志：
- notebook 中所有单元格无报错运行完毕
- 打印出 3 只 ETF 的等权权重（每只约 33.3%）和 10 万元换算
- 对比表包含 4 行（3 只 ETF + 等权组合），3 列指标均为合理数值（非 NaN、非 0）
- 净值曲线图显示 4 条线（3 条灰色线用不同线型区分 + 1 条蓝色实线）
