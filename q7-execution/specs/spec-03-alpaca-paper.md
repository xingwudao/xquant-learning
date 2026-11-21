# spec：怎样从回测走向模拟交易？——Alpaca 模拟交易

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

在 `q7-execution.ipynb` 中已有：
- A 股 ETF 订单生成结果及其与美股的取整偏差对比
- 场内 ETF 的成交价压力测试，以及不计交易成本、计入佣金、计入佣金和滑点这 3 组实验结果

现有结果已经显示数量取整、滑点和交易成本造成的差异。当前需要改用美股 ETF（SPY、QQQ、GLD），连接 Alpaca 数据与模拟交易环境继续检查执行链路。

## 任务目标

完成历史模拟、数据链路比较和 Alpaca 模拟盘下单演示，观察回测假设与模拟交易链路之间的差异。

## 执行要求

1. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.contrib.alpaca.client` – `AlpacaClient`
     - `AlpacaClient(api_key=..., secret_key=..., paper=True)`
     - `get_account()` → `dict`（含 `equity`、`status`）
     - `get_positions()` → `list[dict]`（每项含 `symbol`、`qty`、`avg_entry_price`）
     - `get_order(order_id)` → `dict`（含 `symbol`、`side`、`qty`、`status`）
   - `oxq.contrib.alpaca.market_data` – `AlpacaMarketDataProvider`
     - `AlpacaMarketDataProvider(api_key=..., secret_key=..., feed="iex")`
     - `get_bars(symbol, start, end)` → `DataFrame`
     - `get_bars_multi(symbols, start, end)` → `dict[str, DataFrame]`
   - `oxq.trade.live_broker` – `LiveBroker`
     - `LiveBroker(api_key=..., secret_key=..., paper=True)`
     - `submit_order(order)` → `str`（Alpaca 订单标识符）
     - `get_fills()` → `list[Fill]`
     - `close()` – 关闭 WebSocket 和 HTTP 连接
   - `oxq.core.engine` – `Engine`
     - `Engine().setup(strategy, market=..., broker=..., start=..., end=...)` – 初始化但不运行
     - `Engine.dates` – 迭代用的日期列表
     - `Engine.step(date)` – 处理一条日线行情记录（`bar`）
     - `Engine.result` – 获取结果
   - `oxq.trade.order_generator` – `generate_orders()`
   - `oxq.core.types` – `Position`
   - 策略相关：`make_us_strategy` 和 `make_us_rules` 辅助函数、`Threshold`（信号）、`RiskParityOptimizer`（组合优化器）、`RebalanceFrequencyRule`、`StopLossRule`

2. **A 部分——`SimBroker` 历史模拟比较起点**：
   - 下载美股数据：SPY、QQQ、GLD
   - 固定历史窗口：`START = "2021-01-01"`，`END = "2026-03-18"`，`DOWNLOAD_END = "2026-03-19"`
   - 用 `YFinanceDownloader` 下载时传入 `end=DOWNLOAD_END`，回测和本地读取传入 `end=END`
   - 本地美股数据提供器返回的行情应明确设置 `bars.attrs["currency"] = "USD"`，避免引擎使用默认的人民币标签；这不涉及汇率换算
   - 沿用 spec 02 的策略逻辑和交易规则，将投资对象替换为上述美股 ETF：用 `make_us_strategy(name)` 构造美股策略，用 `make_us_rules()` 构造美股规则
   - 本节各组美股历史模拟均使用 `PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("1"))`，佣金费率为千分之一（0.1%），每笔成交的佣金最低为 1 美元；不沿用 spec 02 的人民币费用。这是教学设定，不代表 Alpaca 的实际收费
   - 用收盘价模式 + 佣金跑一次完整回测，`Engine.run()` 传入 `rules=make_us_rules()`，赋给 `result_sim`
   - 打印累计收益率和成交笔数

3. 定义公共画图函数 `plot_sim_vs_live(norm_sim, norm_live, title, label_sim, label_live)`：
   - 在一张大小为 12 英寸×8 英寸的画布中上下排列 2 个子图，高度比为 3:1，并设置 `layout='constrained'`。
   - 上图绘制 `norm_sim` 和 `norm_live` 这 2 条归一化净值曲线，起点均为 100。图例分别使用 `label_sim` 和 `label_live`。
   - 下图绘制 `norm_live` 减去 `norm_sim` 的差距曲线，并使用 `fill_between` 填充曲线与零线之间的区域。

4. 同时检测 `ALPACA_API_KEY` 和 `ALPACA_SECRET_KEY`。凭据缺失或 B-1 历史数据链路失败时，切换到要求 7 的本地替代方案。B-1 成功后立即将 `result_alpaca` 赋给 `result_live`。B-2 单独处理异常，不覆盖这个历史模拟结果，不自动重试下单。

5. **B-1 部分——数据源差异**（有 Alpaca 时执行）：
   - 用 `AlpacaMarketDataProvider(feed="iex")` 获取 `START` 到 `END` 的同期历史数据。明确当前 Alpaca 链路使用原始价格，而 `YFinanceDownloader` 默认下载调整后价格，本次结果不能只归因于数据提供方
   - 用 `Engine.setup()` 和 `Engine.step()` 逐条处理日线行情记录（`bar`），配合 `SimBroker`
   - 对比 Yahoo Finance 数据和 Alpaca IEX 数据的回测结果
   - 调用 `plot_sim_vs_live()` 画净值曲线对比图，标题“同一策略，不同数据链路”
   - 打印使用 2 个数据源分别进行历史模拟所得的累计收益率及其差值。差值单位为百分点

6. **B-2 部分——模拟盘订单预览与显式提交**：
   - 默认设置 `SUBMIT_PAPER_ORDERS=False`，仅生成并打印计划，不创建 `LiveBroker` 或提交订单
   - 只使用 `paper=True` 的模拟账户。读取当前账户权益、现金、持仓和未结束订单。账户不可交易、有未结束订单，或持仓包含 SPY、QQQ、GLD 之外的投资对象、空头或碎股时，停止本例，不自动清理账户
   - 通过 Alpaca 最新报价接口 `GET https://data.alpaca.markets/v2/stocks/quotes/latest`，指定 `feed="iex"`，读取 SPY、QQQ、GLD 的买价 `bp`、卖价 `ap` 和时间戳 `t`。参考价为买卖报价的中点，不是保证成交价。禁止用固定历史 `END` 或历史日线收盘价替代当前报价
   - 通过模拟盘时钟接口 `GET https://paper-api.alpaca.markets/v2/clock` 检查常规交易时段。本例在闭市、报价缺失、价格无效或报价超过 60 秒时停止，不承诺排队订单下次开盘一定成交。60 秒是本例的安全检查设置，不是市场统一标准
   - 沿用固定示例目标权重 `{"SPY": Decimal("0.35"), "QQQ": Decimal("0.25"), "GLD": Decimal("0.40")}`，用 `generate_orders(..., total_capital=equity, lot_size=1, currency="USD", buying_power=cash)` 计算计划。打印账户标识末 6 位、权益、持仓、参考价、报价时间、买卖方向、股数和预估金额
   - 读者主动开启提交后，再读取账户、持仓和报价，重新计算并展示计划；要求输入 `SUBMIT PAPER` 确认。确认期间报价过期或账户、持仓、未结束订单发生变化时停止，要求重新预览
   - 有可提交计划且通过确认后，才创建 `LiveBroker(paper=True)` 并逐笔提交。任一提交报错或结果未知时，停止后续提交，提示读者在模拟盘核对全部订单，不自动重试或补单
   - 等待 3 秒后，用 `get_order(oid)` 查询已接受订单的状态和已成交数量。已有成交时，打印成交均价、生成本次计划时的参考价及“相对参考价的偏差（%）”，按“（成交均价−参考价）÷参考价”计算
   - 在 `finally` 中关闭连接。打印本次查询到的持仓，不称其为全部订单成交后的“最终持仓”。订单可能等待、部分成交或被拒绝，预览不能保证成交或恰好达到目标权重
   - B-2 只演示订单流程，不产生历史净值，不替换 B-1 已保留的 `result_live`

7. **本地替代方案**（凭据缺失或 B-1 历史数据链路失败时执行）：
   - 沿用 A 部分的佣金设置，另用 `PercentageSlippage(rate=Decimal("0.001"))` 将滑点率设为千分之一（0.1%），同样仅为教学设定
   - 定义美股交易日历：`US_MARKET_CALENDAR = "XNYS"`
   - 用 `SimBroker(fee_model=..., slippage_model=..., fill_price_mode=FillPriceMode.NEXT_OPEN, market_calendar=US_MARKET_CALENDAR)` 按另 1 组模拟执行条件运行历史模拟
   - 调用 `plot_sim_vs_live()` 画 2 组模拟结果的净值曲线对比图
   - 本地替代方案的成书图中，下方子图的纵轴只标“归一化净值差”；在图题前添加图注：“下图的数值为对照模拟的归一化净值减去基准模拟的归一化净值。”
   - 打印 2 组历史模拟结果的累计收益率差
   - 将模拟结果赋给 `result_live`（供第 4 步使用）

## 验收标准

执行成功的标志：
- 单元格无报错运行完毕
- Alpaca 配置正确且相关接口调用成功时，输出必须包含以下 **3 个部分**：
  1. `SimBroker` 历史模拟比较起点的累计收益率
  2. 显示数据源对比图，并输出使用 Alpaca IEX 数据进行历史模拟的累计收益率。
  3. B-2 默认输出当前账户、持仓和订单预览，并明确“未提交”；主动确认提交后，输出提交记录、订单状态、已取得的成交信息和本次查询到的持仓。不符合安全条件时说明停止原因
- 凭据缺失或 B-1 历史数据链路失败时：自动切换到本地替代方案，显示 2 组模拟结果的净值曲线对比图。B-2 异常不得触发自动补单或覆盖 B-1 结果
- `result_live` 变量被赋值，供第 4 步使用。它始终是历史模拟结果，不是 B-2 部分的模拟盘成交记录
- 代码中不硬编码 API key 和 secret key，输出中不显示密钥
- 用模拟接口验证默认预览不提交、取消确认不提交、过期报价或异常账户停止、部分提交后出错停止且不自动重试；不得为验收自动连接读者账户下单
- 本地替代方案的结果及后续执行报告属于历史模拟。复做时按实际数据和模拟条件生成、分析结果，不能把本地历史模拟通过写成 Alpaca 数据接口或模拟盘联调通过
