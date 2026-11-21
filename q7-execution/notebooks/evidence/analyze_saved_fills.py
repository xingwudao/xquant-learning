"""只读分析保存的历史模拟记录；不下载数据、不回测、不连接账户。"""
from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import json

import exchange_calendars as xcals
import pandas as pd
from oxq.core.types import Fill, Order
from oxq.portfolio.execution_report import ExecutionReport


def load_fills(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    result = {}
    for name, rows in raw.items():
        result[name] = []
        for row in rows:
            order = dict(row["order"])
            for field in ("limit_price", "stop_price"):
                if order.get(field) is not None:
                    order[field] = Decimal(order[field])
            result[name].append(Fill(order=Order(**order),
                filled_price=Decimal(row["filled_price"]),
                filled_at=row["filled_at"], fee=Decimal(row["fee"])))
    return result


def aggregate(fills, *, map_previous=False):
    calendar = xcals.get_calendar("XNYS")
    groups = defaultdict(list)
    for fill in fills:
        actual = fill.filled_at[:10]
        comparison = str(calendar.previous_session(pd.Timestamp(actual)).date()) if map_previous else actual
        groups[(comparison, fill.order.symbol, fill.order.side)].append(fill)
    result = {}
    for key, rows in groups.items():
        shares = sum(f.order.shares for f in rows)
        result[key] = dict(fill_date=rows[0].filled_at[:10], shares=shares,
            avg_price=sum((f.filled_price * f.order.shares for f in rows), Decimal(0)) / shares,
            fee=sum((f.fee for f in rows), Decimal(0)))
    return result


def mapped_comparisons(fills):
    base = aggregate(fills["baseline"])
    other = aggregate(fills["comparison"], map_previous=True)
    rows = []
    for day, symbol, side in sorted(base.keys() | other.keys()):
        key = (day, symbol, side)
        b, c = base.get(key), other.get(key)
        row = dict(decision_date=day, symbol=symbol, side=side,
                   match_status="matched" if b and c else "baseline_only" if b else "comparison_only")
        for prefix, value in (("baseline", b), ("comparison", c)):
            for field in ("fill_date", "shares", "avg_price", "fee"):
                row[f"{prefix}_{field}"] = value[field] if value else (0 if field == "shares" else None)
        row["price_difference_rate"] = (c["avg_price"] - b["avg_price"]) / b["avg_price"] if b and c else None
        rows.append(row)
    frame = pd.DataFrame(rows)
    for field in ("baseline_shares", "comparison_shares"):
        frame[field] = frame[field].astype("Int64")
    return frame


def analyze(evidence=None):
    evidence = Path(evidence) if evidence else Path(__file__).resolve().parent
    fills = load_fills(evidence / "M05_simulation_fills.json")
    actual_report = ExecutionReport(sim_fills=fills["baseline"], live_fills=fills["comparison"])
    actual = actual_report.summary()
    actual_reference = pd.read_csv(evidence / "M06_actual_fill_date_comparisons.csv", dtype=str).set_index(["symbol", "date", "side"])
    assert len(actual_reference) == len(actual_report.comparisons)
    for comparison in actual_report.comparisons:
        row = asdict(comparison)
        ref = actual_reference.loc[(row["symbol"], row["date"], row["side"])]
        for field, value in row.items():
            if field not in ("symbol", "date", "side"):
                assert Decimal(str(value)) == Decimal(ref[field]), field
    mapped = mapped_comparisons(fills)
    reference = pd.read_csv(evidence / "M06_event_aligned_fill_comparisons.csv", dtype=str).fillna("")
    reference = reference.set_index(["decision_date", "symbol", "side"])
    assert len(reference) == len(mapped)
    for row in mapped.to_dict("records"):
        ref = reference.loc[(row["decision_date"], row["symbol"], row["side"])]
        for field, value in row.items():
            if field in ("decision_date", "symbol", "side"):
                continue
            if pd.isna(value):
                assert ref[field] == "", field
            elif isinstance(value, Decimal):
                assert value == Decimal(ref[field]), field
            else:
                assert str(value) == ref[field], field
    matched = mapped[mapped.match_status == "matched"].copy()
    rates = matched.price_difference_rate
    fee_diff = sum((f.fee for f in fills["comparison"]), Decimal(0)) - sum((f.fee for f in fills["baseline"]), Decimal(0))
    def number(value, places=2):
        return f"{value:.{places}f}".replace("-", "−")
    def for_display(frame):
        shown = frame.copy()
        for column in shown:
            if column.endswith(("_avg_price", "_fee")):
                shown[column] = shown[column].map(lambda v: "—" if pd.isna(v) else number(v))
        shown["price_difference_rate"] = shown.price_difference_rate.map(lambda v: "—" if pd.isna(v) else number(v * 100) + "%")
        return shown
    print("按实际成交日期汇总：")
    print(f"总对比组数：{actual['total_trades']}；匹配组数：{actual['matched_trades']}；"
          f"仅基准模拟：{actual['sim_only_trades']}；仅对照模拟：{actual['live_only_trades']}")
    print("平均价格差异率：" + (number(actual['avg_price_slippage'] * 100) + "%" if actual['matched_trades'] else "不可计算（无匹配组）"))
    counts = mapped.match_status.value_counts()
    print("按映射日期汇总：")
    print(f"总对比组数：{len(mapped)}；可比较组数：{len(matched)}；"
          f"仅基准模拟：{counts.get('baseline_only', 0)}；仅对照模拟：{counts.get('comparison_only', 0)}")
    if len(matched):
        ordered = sorted(rates)
        n = len(ordered)
        median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
        over = sum(abs(v) > Decimal("0.005") for v in rates)
        print(f"平均价格差异率：{number(sum(rates) / n * 100)}%；中位数：{number(median * 100)}%；"
              f"最小值：{number(min(rates) * 100)}%；最大值：{number(max(rates) * 100)}%")
        print(f"价格差异率绝对值超过 0.5%：{over} 组，占 {over / n:.1%}")
        print("价格差异率绝对值最大的记录：")
        print(for_display(matched.loc[[rates.map(abs).idxmax()]]).iloc[0].to_string())
    print(f"总手续费差异（对照模拟 − 基准模拟）：{number(fee_diff)} 美元")
    print("日期映射后的前 20 条对比记录：")
    print(for_display(mapped.head(20)).to_string(index=False))
    print("比较日期为推定值，不代表同一原始订单；价格差异率不等于真实券商成交滑点。")
    print("原始文件中的 CNY 是遗留标签，本实验价格和费用按美元计；原件未改写，详见 evidence/README.md。")
    return actual_report, mapped


if __name__ == "__main__":
    analyze()
