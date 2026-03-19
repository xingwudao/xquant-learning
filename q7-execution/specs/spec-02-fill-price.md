# Spec: 价格变了怎么办？——成交价压力测试

> 所有命令在沙箱外运行。

## 上下文

在 `q7-execution.ipynb` 中已有：
- Step 1 的订单生成实验（目标权重转具体订单，A 股 vs 美股取整偏差）

当前问题：Step 1 生成了订单"买沪深300ETF 8100 股，按 ¥4.27"。但这是昨天收盘价，现在下单价格已经变了。按哪个价格买？差异有多大影响？

## 任务

在 notebook 中新建代码单元格，用 `FillPriceMode` 的五种模式做压力测试，再用四层成本层叠展示佣金、印花税和滑点的持续侵蚀。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.trade.sim_broker` — `SimBroker` 和 `FillPriceMode` 枚举
     - `FillPriceMode`：`CLOSE`（收盘价）、`NEXT_OPEN`（次日开盘价）、`NEXT_HIGH`（次日最高价）、`NEXT_LOW`（次日最低价）、`MID`（最高与最低均价）
     - `SimBroker(fee_model=..., slippage_model=..., fill_price_mode=...)`
   - `oxq.trade.fees` — `PercentageFee(rate, min_fee)`
   - `oxq.trade.slippage` — `PercentageSlippage(rate)`
   - `oxq.core.Engine` — `Engine().run(strategy, market=..., broker=..., start=..., end=...)`
   - `oxq.data` — `YFinanceDownloader`, `LocalMarketDataProvider`
   - 策略相关：`make_strategy` 辅助函数、`Threshold`（信号）、`RiskParityOptimizer`（组合优化器）、`RebalanceFrequencyRule`、`StopLossRule`
     - `from oxq.signals import Threshold`
     - `from oxq.portfolio.optimizers import RiskParityOptimizer`
     - `from oxq.rules import RebalanceFrequencyRule, StopLossRule`

2. 下载数据并加载：
   - 标的：510300.SS、513100.SS、518880.SS
   - 起始日期：`2021-01-01`，结束：当前日期
   - 用 `YFinanceDownloader` 下载，下载失败时用 try/except 捕获，打印提示并使用本地缓存
   - 用 `LocalMarketDataProvider` 加载

3. 构造策略和规则（风险平价 + 止损，与 Q4 相同逻辑）：
   - 用 `make_strategy(name)` 辅助函数构造策略：创建 `Threshold` 信号，配置 `required_indicators`（RollingVolatility），使用 `RiskParityOptimizer(volatility_col="vol")` 作为 portfolio optimizer
   - 用 `make_rules()` 辅助函数构造规则：`[RebalanceFrequencyRule(interval_days=21), StopLossRule(threshold=0.10)]`
   - 所有 `Engine.run()` 调用需传入 `rules=make_rules()` 参数

4. 五种成交价模式压力测试：
   - 佣金模型：`PercentageFee(rate=Decimal("0.0006"), min_fee=Decimal("5"))`（A 股佣金万一 + 印花税折算，合计约万六）
   - 对五种 `FillPriceMode` 分别创建 SimBroker，跑完整回测
   - 打印对比表：成交价模式、累计收益率、年化收益率、最大回撤、夏普比率、交易次数

5. 画净值曲线图（figsize 12×8，上下两个子图，高度比 3:1）：
   - 上图：五条净值曲线（起点归一化到 100），颜色区分，含图例
   - 下图：与收盘价基准的差距。画四条差距折线（NEXT_OPEN、NEXT_HIGH、NEXT_LOW、MID 各自减去 CLOSE），颜色和上图对应。额外在 NEXT_HIGH 和 NEXT_LOW 之间用浅橙色 `fill_between` 填充，标注"执行不确定性区间"
   - 用 `layout='constrained'` 而非 `plt.tight_layout()`
   - 打印分析：收盘价收益、各模式与理想的差距、最好和最差之间的差距

6. 四层成本层叠分析（次日开盘价模式）：
   - 第一层：无成本 — `SimBroker(fill_price_mode=FillPriceMode.NEXT_OPEN)`
   - 第二层：佣金 — `PercentageFee(rate=Decimal("0.0001"), min_fee=Decimal("5"))`（万一佣金）
   - 第三层：佣金 + 印花税 — `PercentageFee(rate=Decimal("0.0006"), min_fee=Decimal("5"))`（万一佣金 + 卖出印花税 0.05% 折算为双边约万五，合计约万六）
   - 第四层：佣金 + 印花税 + 滑点 — 上述费率 + `PercentageSlippage(rate=Decimal("0.001"))`
   - 打印对比表：成本层级、累计收益率、年化收益率、夏普比率
   - 打印说明：印花税实际只在卖出时收取 0.05%，这里用 PercentageFee 近似折算为双边费率，实际成本略有差异

7. 画成本层叠图（figsize 12×8，上下两个子图，高度比 3:1）：
   - 先将四条权益曲线归一化到起点=100（`equity / equity.iloc[0] * 100`），对齐到公共交易日
   - 上图：四条归一化净值曲线
   - 下图：成本侵蚀折线——第二/三/四层的归一化净值分别减去"无成本"的归一化净值。三条差距线应始终 <= 0（成本只会减少收益），如果出现正值说明计算有误
   - 用 `layout='constrained'`
   - 打印成本侵蚀分解：佣金贡献、印花税贡献、滑点贡献
   - 过渡：这些都是估算，真实执行到底差多少？

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 五种成交价模式的对比表有 5 行，含收益和夏普
- 净值曲线图展示五条线和执行不确定性区间填充
- 成本层叠表有 4 行，成本逐层递增时收益逐层递减
- 成本层叠图展示四条线和成本侵蚀曲线
