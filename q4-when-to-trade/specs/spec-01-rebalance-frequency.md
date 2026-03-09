# Spec: 调仓频率——多久调一次才合适？

> 所有命令在沙箱外运行。

## 上下文

本章探讨"什么时候买卖"。Q3 用了三种信号（等权、风险平价、动量排名）。本章选择风险平价（RiskParity）作为基础信号——它始终持有全部 3 只 ETF，方便我们观察止损和止盈规则的效果。Q3 每 10 个交易日调一次仓，但为什么是 10 天？调得更勤或更懒，结果会怎样？

## 任务

在 notebook `q4-when-to-trade.ipynb` 中创建代码，对比不同调仓频率的效果，并首次引入交易成本。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.trade.PercentageFee`
   - `oxq.trade.SimBroker`（重点关注 `fee_model` 参数）
   - `oxq.rules.RebalanceRule`
   - `oxq.core.Engine`、`oxq.core.Strategy`

3. 创建 notebook `q4-when-to-trade.ipynb`，导入所需库并设置中文显示：
   - `from oxq.core import Engine, Strategy`
   - `from oxq.data import YFinanceDownloader, LocalMarketDataProvider`
   - `from oxq.indicators import RollingVolatility`
   - `from oxq.signals import RiskParity`
   - `from oxq.rules import RebalanceRule`
   - `from oxq.trade import SimBroker, PercentageFee`
   - `from oxq.universe import StaticUniverse`
   - pandas, numpy, matplotlib.pyplot, Decimal
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 复用 Q3 的数据和策略配置：
   - `SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - `SYMBOL_NAMES = {"510300.SS": "沪深300ETF", "513100.SS": "纳指100ETF", "518880.SS": "黄金ETF"}`
   - 数据起始日期 `START = "2021-01-01"`
   - 使用 `YFinanceDownloader` 下载数据
   - 构建 `StaticUniverse`，加载数据并预计算 vol 指标
   - RiskParity 信号（vol="vol"）

5. 定义公共策略配置 COMMON 字典（包含 universe、indicators、signals、entry_rules=[]、exit_rules=[]），供后续 spec 复用。

6. 定义 4 种调仓频率：`FREQUENCIES = [5, 10, 21, 63]`，分别对应约每周、两周、每月、每季度。

7. 第一轮回测——不含成本（`SimBroker()`）：
   - 循环跑 4 种频率的回测
   - 打印对比表：频率、累计收益率、年化波动率、最大回撤、夏普比率、交易次数

8. 第二轮回测——含成本（`SimBroker(fee_model=PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5")))`）：
   - 循环跑 4 种频率的回测
   - 打印对比表：频率、累计收益率、年化波动率、最大回撤、夏普比率、交易次数、总手续费
   - 总手续费计算：`sum(f.fee for f in result.trades)`

9. 画净值曲线对比图（figsize 12x6）：
   - 4 条线对应 4 种频率（含成本版本）
   - 归一化到起点 = 100
   - 标题「调仓频率对比（含交易成本）」

10. 打印分析（根据实际数据动态描述方向，不要硬写"更高"或"更低"）：
    - 不含成本时，哪个频率效果最好？
    - 加上成本后，排名有没有变化？
    - 交易次数和总手续费随频率的变化规律
    - 「每次调仓都不是免费的——佣金和手续费是实打实的钱。频率越高，交易越多，成本越大。」
    - 「但频率的选择不是最关键的问题。更要命的是——两次调仓之间如果某只 ETF 暴跌，你只能干等到下一个调仓日。能不能加一个'紧急出口'？」

## 结果呈现

1. 无成本对比表（4 行，6 列）
2. 含成本对比表（4 行，7 列，多一列"总手续费"）
3. 含成本净值曲线对比图
4. 分析文字

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 无成本和含成本各有 4 行对比数据
- 含成本表多一列总手续费，手续费随频率增大而增大
- 净值曲线图显示 4 条线
