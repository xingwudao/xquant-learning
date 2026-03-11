# Spec: 回测 vs 实盘，差距有多大？——Alpaca 模拟交易

> 所有命令在沙箱外运行。

## 上下文

在 `q7-execution.ipynb` 中已有：
- Step 1 的订单生成实验（取整偏差）
- Step 2 的成交价压力测试和成本层叠

前两步用模拟方式暴露了取整偏差、滑点和成本，但都是"估算"。现在要接入 Alpaca 模拟交易平台，让策略真正跑一遍，看看回测和实盘到底差多少。

## 任务

在 notebook 中新建代码单元格，先用 SimBroker 跑一次回测作为基准，再接入 Alpaca 模拟盘做两件事：(1) 用 Alpaca 数据源回测，看数据差异；(2) 用 LiveBroker 提交真实订单，看执行差异。无 Alpaca 账号时提供替代方案。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.contrib.alpaca.client` — `AlpacaClient`
     - `AlpacaClient(api_key=..., secret_key=..., paper=True)`
     - `get_account()` → dict（含 `equity`, `status`）
     - `get_positions()` → list[dict]（每项含 `symbol`, `qty`, `avg_entry_price`）
     - `get_order(order_id)` → dict（含 `symbol`, `side`, `qty`, `status`）
   - `oxq.contrib.alpaca.market_data` — `AlpacaMarketDataProvider`
     - `AlpacaMarketDataProvider(api_key=..., secret_key=..., feed="iex")`
     - `get_bars(symbol, start, end)` → DataFrame
     - `get_bars_multi(symbols, start, end)` → dict[str, DataFrame]
   - `oxq.trade.live_broker` — `LiveBroker`
     - `LiveBroker(api_key=..., secret_key=..., paper=True)`
     - `submit_order(order)` → str（Alpaca 订单 ID）
     - `get_fills()` → list[Fill]
     - `close()` — 关闭 WebSocket 和 HTTP 连接
   - `oxq.core.engine` — `Engine`
     - `Engine().setup(strategy, market=..., broker=..., start=..., end=...)` — 初始化但不运行
     - `Engine.dates` — 迭代用的日期列表
     - `Engine.step(date)` — 执行单个 bar
     - `Engine.result` — 获取结果
   - `oxq.trade.order_generator` — `generate_orders()`
   - `oxq.core.types` — `Position`

2. Part A——SimBroker 回测基准：
   - 复用 Step 2 的策略定义和数据
   - 用收盘价模式 + 佣金跑一次完整回测
   - 打印累计收益和交易笔数

3. Part B——Alpaca 模拟盘（需要环境变量 `ALPACA_API_KEY` 和 `ALPACA_SECRET_KEY`）：
   - 用 `os.environ.get("ALPACA_API_KEY")` 检测是否有 Alpaca 账号
   - 全部 Alpaca 操作包在 try/except 中，失败时自动切换到替代方案

4. Part B-1——数据源差异：
   - 用 `AlpacaMarketDataProvider(feed="iex")` 获取同期历史数据
   - 用 `Engine.setup()` + `Engine.step()` 逐 bar 执行，配合 SimBroker
   - 对比 YFinance 数据和 Alpaca IEX 数据的回测结果
   - 画净值对比图（上下两个子图：上面净值曲线，下面执行落差），标题"同一策略，不同数据源"
   - 打印数据源差异

5. Part B-2——LiveBroker 实盘演示：
   - 用 `AlpacaClient.get_positions()` 获取当前持仓，转为 `Position` 对象
   - 用 `AlpacaMarketDataProvider.get_bars_multi()` 获取最新价格
   - 用 `generate_orders()` 生成调仓订单
   - 用 `LiveBroker(paper=True)` 提交订单
   - 等待 3 秒后调用 `get_fills()` 获取成交回报
   - 打印成交表格：标的、方向、股数、成交价、回测价、滑点
   - 如果没有成交（市场关闭），查询订单状态并打印
   - 调用 `live_broker.close()` 关闭连接
   - 查看最终持仓
   - 将 Alpaca 数据的回测结果赋给 `result_live`（供 Step 4 使用）

6. 无 Alpaca 替代方案：
   - 用 `SimBroker(fee_model=..., slippage_model=..., fill_price_mode=FillPriceMode.NEXT_OPEN)` 模拟实盘
   - 画回测 vs 模拟实盘的净值对比图
   - 打印执行落差（implementation shortfall）
   - 将模拟结果赋给 `result_live`（供 Step 4 使用）

7. 画图用的公共函数 `plot_sim_vs_live(norm_sim, norm_live, title, label_sim, label_live)`：
   - 上图：两条净值曲线
   - 下图：差距填充图
   - `layout='constrained'`

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 有 Alpaca 时：显示账户状态、数据源对比图、LiveBroker 订单提交结果
- 无 Alpaca 时：自动切换到替代方案，显示模拟实盘的净值对比图
- `result_live` 变量被赋值，供 Step 4 使用
- 不包含任何硬编码的 API Key
