# Spec: 35% 是多少股？——目标权重转具体订单

> 所有命令在沙箱外运行。

## 上下文

学员跑完 Q6，策略通过了所有检验。今天是调仓日，风险平价信号给出目标权重：沪深300ETF 35% / 纳指100ETF 25% / 黄金ETF 40%。打开券商 APP——只能输入股数和价格。35% 是多少股？

## 任务

在 notebook `q7-execution.ipynb` 中创建代码，用 `generate_orders()` 把目标权重翻译成具体订单，并对比 A 股（lot_size=100）和美股（lot_size=1）的取整偏差。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.trade.order_generator` — `generate_orders()` 函数和 `PlannedOrder` 数据类
     - `generate_orders(target_weights, positions, prices, total_capital, lot_size)` -- `list[PlannedOrder]`
     - `PlannedOrder` 属性：`order`（Order 对象）、`current_shares`、`target_shares`、`current_weight`、`target_weight`、`estimated_amount`
   - `oxq.core.types` — `Position` 数据类（`symbol`, `shares`, `avg_cost`）

3. 创建 notebook `q7-execution.ipynb`，导入所需库并设置中文显示：
   - `from oxq.trade import generate_orders, PlannedOrder`
   - `from oxq.core.types import Position`
   - `from decimal import Decimal`
   - pandas, numpy, matplotlib.pyplot
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 定义常量：
   - A 股标的：`SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 中文名映射：`SYMBOL_NAMES = {"510300.SS": "沪深300ETF", "513100.SS": "纳指100ETF", "518880.SS": "黄金ETF"}`
   - 目标权重：沪深300ETF 35%、纳指100ETF 25%、黄金ETF 40%
   - 模拟价格（近期收盘价）：510300.SS ¥4.27、513100.SS ¥1.72、518880.SS ¥8.04

5. 第一步——从空仓开始生成 A 股订单：
   - 10 万人民币，`lot_size=100`，空仓（`positions={}`）
   - 打印订单表格：标的（中文名）、方向、目标股数、预估金额、目标权重、实际权重、偏差
   - 计算并打印投入金额和剩余现金（残余占比）

6. 第二步——A 股 vs 美股取整偏差对比：
   - 美股标的和价格：SPY $593.12、QQQ $512.30、GLD $298.50
   - 美股 10 万美元，`lot_size=1`
   - 对比表格：目标权重 -- A 股（股数/实际权重/偏差）vs 美股（股数/实际权重/偏差）
   - 打印两个市场的现金残余

7. 第三步——资金量对取整偏差的影响：
   - 统一资金档位：1 万、5 万、10 万、50 万、100 万
   - 分别计算 A 股（lot_size=100）和美股（lot_size=1）在各资金量下的最大权重偏差和现金残余
   - 打印两张表格（A 股/美股各一张）

8. 画一张图（figsize 14×5，两个子图并排）：
   - 左图：A 股 vs 美股的最大权重偏差随资金量变化（分组柱状图）
   - 右图：A 股 vs 美股的现金残余占比随资金量变化（分组柱状图）
   - A 股红色、美股蓝色

9. 打印分析：
   - 回测的权重精确到小数点后 N 位，现实只能买整数股
   - A 股 100 股整手约束让偏差远大于美股的 1 股单位
   - 资金量越小，偏差越大
   - 过渡：订单有了，但按什么价格下单？

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- A 股订单表格显示 3 只 ETF 的目标股数、实际权重与偏差
- A 股 vs 美股对比表展示取整偏差差异
- 柱状图直观展示资金量和市场对偏差的影响
- 剩余现金（现金残余）有明确数值
