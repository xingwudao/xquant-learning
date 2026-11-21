# 第3步实现参考，依赖 Notebook 前两步；不会由只读复核单元自动执行
# 重新实验可能下载行情和读取模拟账户，请先阅读 evidence/README.md
import os
import time
import matplotlib.dates as mdates

# ══════════════════════════════════════════════
# 第 3 步使用美股 ETF（SPY、QQQ、GLD）+ Alpaca
# 需要重新下载美股数据和构造美股策略
# ══════════════════════════════════════════════
US_SYMS = ("SPY", "QQQ", "GLD")
US_SYM_NAMES = {"SPY": "标普 500 ETF", "QQQ": "纳指 100 ETF", "GLD": "黄金 ETF"}
US_MARKET_CALENDAR = "XNYS"
US_TW = {
    "SPY": Decimal("0.35"),
    "QQQ": Decimal("0.25"),
    "GLD": Decimal("0.40"),
}

# 下载美股数据
for sym in US_SYMS:
    try:
        downloader.download(sym, start=START, end=DOWNLOAD_END)
    except Exception as e:
        print(f"  {sym} 下载失败（{e}），使用本地缓存")

print("美股数据加载完成")
class USLocalMarketDataProvider(LocalMarketDataProvider):
    def get_bars(self, symbol, start, end):
        bars = super().get_bars(symbol, start, end).copy()
        bars.attrs["currency"] = "USD"
        return bars

us_market = USLocalMarketDataProvider()
for sym in US_SYMS:
    bars = us_market.get_bars(sym, START, END)
    print(f"  {US_SYM_NAMES[sym]}({sym}): {len(bars)} 个交易日")

# 构造美股策略（与第 2 步相同逻辑，换标的）
us_universe = StaticUniverse(symbols=US_SYMS, name="us-macro-etf")

def make_us_strategy(name):
    signal = Threshold()
    signal.required_indicators = {
        "vol": (RollingVolatility(), {"column": "close", "period": 20}),
    }
    return Strategy(
        name=name,
        universe=us_universe,
        signals={"active": (signal, {"column": "close", "threshold": 0, "relationship": "gt"})},
        portfolio=RiskParityOptimizer(volatility_col="vol"),
    )

def make_us_rules():
    return [RebalanceFrequencyRule(interval_days=BEST_FREQ), StopLossRule(threshold=BEST_SL)]

# 美股佣金模型
US_FEE_MODEL = PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("1"))

# ══════════════════════════════════════════════
# A 部分：SimBroker 回测（比较起点）
# ══════════════════════════════════════════════
broker_sim = SimBroker(fee_model=US_FEE_MODEL, fill_price_mode=FillPriceMode.CLOSE)
result_sim = Engine().run(
    make_us_strategy("sim-baseline"),
    market=USLocalMarketDataProvider(),
    broker=broker_sim,
    start=START,
    end=END,
    rules=make_us_rules(),
)
print(f"\nSimBroker 回测完成：累计收益率 {result_sim.total_return():.2%}，{len(result_sim.trades)} 笔成交")

# ══════════════════════════════════════════════
# B 部分：Alpaca 数据与模拟盘
# ══════════════════════════════════════════════
HAS_ALPACA = bool(os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY"))
ALPACA_OK = False

def plot_sim_vs_live(norm_sim, norm_live, title, label_sim, label_live):
    """上下两图：上面是归一化净值曲线，下面是对照模拟减去基准模拟的归一化净值差。"""
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1],
                                          sharex=True, layout='constrained')
    ax_top.plot(norm_sim.index, norm_sim.values, label=label_sim, color='#3498DB', linewidth=2)
    ax_top.plot(norm_live.index, norm_live.values, label=label_live, color='#E74C3C', linestyle='--', linewidth=2)
    ax_top.axhline(y=100, color='black', linestyle='-', linewidth=0.5)
    ax_top.set_ylabel('归一化净值（起点 = 100）')
    ax_top.set_title(title)
    ax_top.legend()
    ax_top.grid(True, alpha=0.3)

    gap = norm_live - norm_sim
    ax_bot.fill_between(gap.index, 0, gap.values, alpha=0.4, color='#E74C3C', label='对照模拟 − 基准模拟')
    ax_bot.plot(gap.index, gap.values, color='#E74C3C', linewidth=1)
    ax_bot.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax_bot.set_ylabel('归一化净值差')
    ax_bot.set_xlabel('年份')
    ax_bot.xaxis.set_major_locator(mdates.YearLocator())
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_bot.legend(loc='lower left', fontsize=8)
    ax_bot.grid(True, alpha=0.3)

    plt.show()

# B-2 只连接模拟盘。默认预览；修改开关后仍需确认本次计划。
SUBMIT_PAPER_ORDERS = False

class PaperPreviewStop(ValueError):
    """本例主动停止操作的可公开说明，不包含密钥或接口响应。"""
    pass

def current_paper_snapshot(client):
    """只读当前账户和 IEX 报价；不使用历史回测 END 作为下单价格。"""
    import httpx
    headers = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
               "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
    with httpx.Client(headers=headers, timeout=15) as http:
        clock = http.get("https://paper-api.alpaca.markets/v2/clock")
        clock.raise_for_status()
        response = http.get("https://data.alpaca.markets/v2/stocks/quotes/latest",
                            params={"symbols": ",".join(US_SYMS), "feed": "iex"})
        response.raise_for_status()
        quotes = response.json()["quotes"]
    account = client.get_account()
    positions = client.get_positions()
    if account.get("status") != "ACTIVE" or account.get("trading_blocked") or account.get("account_blocked"):
        raise PaperPreviewStop("账户不可交易")
    if not clock.json().get("is_open"):
        raise PaperPreviewStop("当前不在常规交易时段，本例暂不生成或提交订单")
    if client.list_open_orders():
        raise PaperPreviewStop("账户有未结束的订单，请先核对，勿重复提交")
    prices, timestamps, converted = {}, {}, {}
    for symbol in US_SYMS:
        quote = quotes[symbol]
        bid, ask = Decimal(str(quote['bp'])), Decimal(str(quote['ap']))
        stamp = pd.Timestamp(quote['t'])
        age = (pd.Timestamp.now(tz='UTC') - stamp).total_seconds()
        if not bid.is_finite() or not ask.is_finite() or bid <= 0 or ask < bid or not 0 <= age <= 60:
            raise PaperPreviewStop("报价缺失、无效或超过 60 秒，请稍后重新预览")
        prices[symbol] = (bid + ask) / 2
        timestamps[symbol] = stamp
    for position in positions:
        symbol, qty = position['symbol'], Decimal(position['qty'])
        if symbol not in US_SYMS or not qty.is_finite() or qty < 0 or qty != qty.to_integral_value():
            raise PaperPreviewStop("本例仅处理 SPY、QQQ、GLD 的非负整数股持仓，请使用专用模拟账户")
        converted[symbol] = Position(symbol=symbol, shares=int(qty), avg_cost=Decimal(position['avg_entry_price']))
    equity = Decimal(account['equity'])
    cash = Decimal(account['cash'])
    if not equity.is_finite() or equity <= 0 or not cash.is_finite() or cash < 0:
        raise PaperPreviewStop("账户权益或现金不符合本例不借款的条件")
    planned = generate_orders(US_TW, converted, prices, total_capital=equity,
                              lot_size=1, currency='USD', buying_power=cash)
    return account, converted, prices, timestamps, planned

def show_paper_plan(snapshot):
    account, positions, prices, timestamps, planned = snapshot
    print(f"模拟盘账户尾号：{str(account.get('id', ''))[-6:]}；账户权益：{Decimal(account['equity']):.2f} 美元")
    print("当前持仓：", {s:p.shares for s,p in positions.items()})
    for symbol in US_SYMS:
        print(f"{symbol} 参考价：{prices[symbol]:.4f} 美元；报价时间：{timestamps[symbol]}")
    print("参考价为最新 IEX 买卖报价的中点，不是保证成交价。")
    for item in planned:
        side = '买入' if item.order.side == 'BUY' else '卖出'
        print(f"{item.order.symbol} {side} {item.order.shares} 股，预估金额：{item.estimated_amount:.2f} 美元")
    if not planned:
        print("当前计算没有可提交的调整订单；整数股和可用资金会限制实际权重。")

def paper_order_demo(client, broker_factory, *, submit=False,
                     snapshot_reader=current_paper_snapshot, confirm=input, wait=time.sleep):
    print("\nB-2：Alpaca 模拟盘订单预览")
    snapshot = snapshot_reader(client)
    show_paper_plan(snapshot)
    if not submit:
        print("仅预览，未提交订单。需主动开启 SUBMIT_PAPER_ORDERS，并确认刷新后的计划。")
        return []
    # 真正提交前重新读取账户、持仓和报价，并展示新计划。
    snapshot = snapshot_reader(client)
    show_paper_plan(snapshot)
    account, positions, prices, timestamps, planned = snapshot
    if not planned or confirm('确认以上模拟盘计划请输入 SUBMIT PAPER，其他输入均取消：') != 'SUBMIT PAPER':
        print("本次未提交订单。")
        return []
    # 人工确认期间可能经过较长时间或发生持仓变化，不能盲用旧预览。
    if any((pd.Timestamp.now(tz='UTC') - t).total_seconds() > 60 for t in timestamps.values()):
        raise PaperPreviewStop("确认时报价已经过期，请重新预览")
    current = client.get_account()
    now_positions = {p['symbol']:Decimal(p['qty']) for p in client.get_positions()}
    expected = {s:Decimal(p.shares) for s,p in positions.items()}
    if (current.get('id') != account.get('id') or current.get('status') != 'ACTIVE'
            or current.get('trading_blocked') or current.get('account_blocked')
            or Decimal(current['cash']) != Decimal(account['cash'])
            or now_positions != expected or client.list_open_orders()):
        raise PaperPreviewStop("账户或订单状态已变化，请重新预览")
    order_ids = []
    broker = broker_factory(paper=True)
    try:
        for item in planned:
            try:
                oid = broker.submit_order(item.order)
                order_ids.append(oid)
                print(f"已接受订单：{item.order.symbol}；订单编号：{oid}")
            except Exception:
                print("提交结果异常或未知，已停止后续提交。请到模拟盘核对全部订单，勿直接重跑或自动补单。")
                break
        if order_ids:
            wait(3)
            for oid in order_ids:
                try:
                    info = client.get_order(oid)
                    print(f"订单 {oid}：{info['status']}，已成交 {info.get('filled_qty', '0')} 股")
                    if info.get('filled_avg_price') and Decimal(info.get('filled_qty', '0')) > 0:
                        price = Decimal(info['filled_avg_price'])
                        ref = prices[info['symbol']]
                        deviation = (price-ref)/ref
                        print(f"{info['symbol']} 成交均价：{price:.4f} 美元；参考价：{ref:.4f} 美元；相对参考价的偏差：{deviation:+.2%}")
                except Exception:
                    print(f"订单 {oid} 状态查询失败，请到模拟盘核对。")
            print("本次查询到的持仓（不代表所有订单均已成交）：", client.get_positions())
    finally:
        broker.close()
    return order_ids

client = None
if HAS_ALPACA:
    try:
        from oxq.contrib.alpaca import AlpacaClient, AlpacaMarketDataProvider
        from oxq.trade import LiveBroker

        # 初始化 Alpaca（默认 feed="iex"，免费账户可用）
        client = AlpacaClient(paper=True)
        alpaca_market = AlpacaMarketDataProvider()

        account = client.get_account()
        print(f"\nAlpaca 账户状态：{account.get('status')}")
        print(f"账户权益：${float(account.get('equity', 0)):,.2f}")

        # ── B-1 部分：历史对比（Alpaca 数据 + SimBroker） ──
        alpaca_bars = alpaca_market.get_bars_multi(list(US_SYMS), start=START, end=END)
        for sym in US_SYMS:
            print(f"  {sym}: {len(alpaca_bars[sym])} 个交易日")

        engine_alpaca = Engine()
        engine_alpaca.setup(
            make_us_strategy("alpaca-data"),
            market=alpaca_market,
            broker=SimBroker(fee_model=US_FEE_MODEL, fill_price_mode=FillPriceMode.CLOSE),
            start=START,
            end=END,
            rules=make_us_rules(),
        )
        for date in engine_alpaca.dates:
            engine_alpaca.step(date)
        result_alpaca = engine_alpaca.result
        print(f"\nAlpaca 数据 + SimBroker 回测：累计收益率 {result_alpaca.total_return():.2%}，"
              f"{len(result_alpaca.trades)} 笔成交")

        # 净值曲线对比
        eq_sim = pd.Series(dict(result_sim.equity_curve))
        eq_alpaca = pd.Series(dict(result_alpaca.equity_curve))
        common = eq_sim.index.intersection(eq_alpaca.index)
        eq_sim_c = eq_sim.reindex(common).dropna()
        eq_alpaca_c = eq_alpaca.reindex(common).dropna()
        norm_sim_plot = eq_sim_c / eq_sim_c.iloc[0] * 100
        norm_alpaca_plot = eq_alpaca_c / eq_alpaca_c.iloc[0] * 100

        plot_sim_vs_live(norm_sim_plot, norm_alpaca_plot,
                         '同一策略，不同数据链路',
                         'Yahoo Finance 数据', 'Alpaca IEX 数据')

        fig_path = "../book/images/04-data-source-comparison.png"
        # 重新画一次保存
        fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1],
                                              sharex=True, layout='constrained')
        ax_top.plot(norm_sim_plot.index, norm_sim_plot.values, label='Yahoo Finance 数据', color='#3498DB', linewidth=2)
        ax_top.plot(norm_alpaca_plot.index, norm_alpaca_plot.values, label='Alpaca IEX 数据', color='#E74C3C', linestyle='--', linewidth=2)
        ax_top.axhline(y=100, color='black', linestyle='-', linewidth=0.5)
        ax_top.set_ylabel('归一化净值（起点 = 100）')
        ax_top.set_title('同一策略，不同数据链路')
        ax_top.legend()
        ax_top.grid(True, alpha=0.3)
        gap = norm_alpaca_plot - norm_sim_plot
        ax_bot.fill_between(gap.index, 0, gap.values, alpha=0.4, color='#E74C3C', label='归一化净值差')
        ax_bot.plot(gap.index, gap.values, color='#E74C3C', linewidth=1)
        ax_bot.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax_bot.set_ylabel('归一化净值差')
        ax_bot.set_xlabel('年份')
        ax_bot.xaxis.set_major_locator(mdates.YearLocator())
        ax_bot.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax_bot.legend(loc='lower left', fontsize=8)
        ax_bot.grid(True, alpha=0.3)
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()

        data_gap = result_sim.total_return() - result_alpaca.total_return()
        print(f"\nYFinance 回测：{result_sim.total_return():.2%}")
        print(f"使用 Alpaca IEX 数据进行历史模拟的累计收益率：{result_alpaca.total_return():.2%}")
        print(f"两条数据链路的累计收益率相差：{data_gap * 100:.2f} 个百分点")
        print(f"当前比较还同时包含价格口径差异，结果不能只归因于数据提供方。")

        # B-1 的历史结果与 B-2 的当前账户操作相互独立。
        result_live = result_alpaca
        ALPACA_OK = True
        try:
            paper_order_demo(client, LiveBroker, submit=SUBMIT_PAPER_ORDERS)
        except PaperPreviewStop as error:
            print(f"B-2 已停止：{error}。未自动重试下单，B-1 历史结果保留。")
        except Exception as error:
            print(f"B-2 已停止（{type(error).__name__}）。请核对账户、报价和平台订单状态；不会自动重试下单。")
    except Exception as error:
        print(f"B-1 历史数据链路失败（{type(error).__name__}），使用本地替代方案。")
    finally:
        if client is not None:
            client.close()

if not HAS_ALPACA:
    print("\nAlpaca 所需的 API key 或 secret key 未配置完整。")
    print("\n如果你有 Alpaca 账号，请设置环境变量后重新运行：")
    print("  export ALPACA_API_KEY='你的API key'")
    print("  export ALPACA_SECRET_KEY='你的secret key'")

if not ALPACA_OK:
    print("\n没有 Alpaca 也没关系——我们用 NEXT_OPEN 模式生成另一组历史模拟结果：")

    US_SLIPPAGE = PercentageSlippage(rate=Decimal("0.001"))
    broker_pseudo_live = SimBroker(fee_model=US_FEE_MODEL, slippage_model=US_SLIPPAGE,
                                   fill_price_mode=FillPriceMode.NEXT_OPEN,
                                   market_calendar=US_MARKET_CALENDAR)
    result_live = Engine().run(
        make_us_strategy("pseudo-live"),
        market=USLocalMarketDataProvider(),
        broker=broker_pseudo_live,
        start=START,
        end=END,
        rules=make_us_rules(),
    )

    print(f"\n对照模拟完成：累计收益率 {result_live.total_return():.2%}，{len(result_live.trades)} 笔成交")

    eq_sim = pd.Series(dict(result_sim.equity_curve))
    eq_live = pd.Series(dict(result_live.equity_curve))
    common = eq_sim.index.intersection(eq_live.index)
    eq_sim = eq_sim.reindex(common).dropna()
    eq_live = eq_live.reindex(common).dropna()
    norm_sim_plot = eq_sim / eq_sim.iloc[0] * 100
    norm_live_plot = eq_live / eq_live.iloc[0] * 100

    plot_sim_vs_live(norm_sim_plot, norm_live_plot,
                     '收盘价回测与次日开盘价对照模拟',
                     '收盘价成交，计入佣金',
                     '次日开盘价成交，计入佣金和滑点')

    # 保存图片
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1],
                                          sharex=True, layout='constrained')
    ax_top.plot(norm_sim_plot.index, norm_sim_plot.values, label='收盘价成交，计入佣金', color='#3498DB', linewidth=2)
    ax_top.plot(norm_live_plot.index, norm_live_plot.values, label='次日开盘价成交，计入佣金和滑点', color='#E74C3C', linestyle='--', linewidth=2)
    ax_top.axhline(y=100, color='black', linestyle='-', linewidth=0.5)
    ax_top.set_ylabel('归一化净值（起点 = 100）')
    ax_top.set_title('收盘价回测与次日开盘价对照模拟')
    ax_top.legend()
    ax_top.grid(True, alpha=0.3)
    gap = norm_live_plot - norm_sim_plot
    ax_bot.fill_between(gap.index, 0, gap.values, alpha=0.4, color='#E74C3C', label='对照模拟 − 基准模拟')
    ax_bot.plot(gap.index, gap.values, color='#E74C3C', linewidth=1)
    ax_bot.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax_bot.set_ylabel('归一化净值差')
    ax_bot.set_xlabel('年份')
    ax_bot.xaxis.set_major_locator(mdates.YearLocator())
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_bot.legend(loc='lower left', fontsize=8)
    ax_bot.grid(True, alpha=0.3)
    plt.savefig("../book/images/04-data-source-comparison.png", dpi=150, bbox_inches='tight')
    plt.close()

    gap = result_sim.total_return() - result_live.total_return()
    print(f"\n基准模拟（按收盘价成交）累计收益率：{result_sim.total_return():.2%}")
    print(f"对照模拟累计收益率：{result_live.total_return():.2%}")
    print(f"累计收益率差（基准模拟 − 对照模拟）：{gap * 100:.2f} 个百分点")
    print(f"\n这只是两组历史模拟设定的结果差异，不是实际执行落差。")
    print(f"Alpaca 模拟盘与真钱交易的结果还会受订单状态、成交机制和市场条件影响，不能由这组历史模拟直接推断。")
