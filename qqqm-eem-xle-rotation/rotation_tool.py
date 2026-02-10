#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import yfinance as yf

TICKERS = ["QQQM", "EEM", "XLE"]
ROTATE_THRESHOLD = 0.03
MOMENTUM_MONTHS = 6
REBASE_MONTHS = 36
DELTA = 0.10
FLOOR = 0.10
CAP = 0.60
REQUIRE_TWO_MONTH_CONFIRMATION = False


def fetch_month_end_prices(tickers):
    daily = yf.download(
        tickers,
        period="max",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if daily.empty:
        raise RuntimeError("No price data returned from yfinance.")

    if isinstance(daily.columns, pd.MultiIndex):
        close = daily["Close"].copy()
    else:
        close = daily[["Close"]].copy()
        close.columns = [tickers[0]]

    try:
        monthly = close.resample("ME").last()
    except ValueError:
        monthly = close.resample("M").last()
    monthly = monthly.dropna(how="all")

    return monthly


def compute_indicators(monthly):
    sma10 = monthly.rolling(10).mean()
    trend_on = monthly > sma10
    momentum = monthly / monthly.shift(MOMENTUM_MONTHS) - 1
    return sma10, trend_on, momentum


def donor_key(ticker, trend_row, momentum_row):
    trend_val = trend_row[ticker]
    if pd.isna(trend_val):
        trend_rank = 2
    elif bool(trend_val):
        trend_rank = 1
    else:
        trend_rank = 0
    return (trend_rank, momentum_row[ticker])


def suggest_action(leader, trend_row, momentum_row):
    candidates = [
        t for t in TICKERS if t != leader and not pd.isna(momentum_row[t])
    ]
    if not candidates:
        return None, "no_donor"
    candidates = sorted(candidates, key=lambda t: donor_key(t, trend_row, momentum_row))
    return {"from": candidates[0], "to": leader, "amount": DELTA}, None


def simulate(monthly, trend_on, momentum12):
    prev_leader = None
    prev_top = None
    decisions = []

    for idx, dt in enumerate(monthly.index):
        row_trend = trend_on.iloc[idx]
        row_mom = momentum12.iloc[idx]
        if row_trend.isna().all() or row_mom.isna().all():
            continue

        candidates = []
        for t in monthly.columns:
            trend_val = row_trend[t]
            if pd.isna(trend_val) or not bool(trend_val):
                continue
            if pd.isna(row_mom[t]):
                continue
            candidates.append(t)
        ranked = sorted(candidates, key=lambda t: row_mom[t], reverse=True)
        top = ranked[0] if ranked else None
        prev_leader_before = prev_leader
        rotate_diff = None
        change_event = False
        confirm_ok = True
        action = None
        block_reason = None

        if top is None:
            change_reason = "no_trend_on"
        elif prev_leader is None:
            prev_leader = top
            change_reason = "init_leader"
        elif top == prev_leader:
            change_reason = "leader_unchanged"
        else:
            if pd.isna(row_mom[prev_leader]):
                change_reason = "prev_leader_momentum_na"
            else:
                rotate_diff = row_mom[top] - row_mom[prev_leader]
                if REQUIRE_TWO_MONTH_CONFIRMATION:
                    confirm_ok = top == prev_top
                if rotate_diff >= ROTATE_THRESHOLD and confirm_ok:
                    change_event = True
                    change_reason = "triggered"
                elif rotate_diff < ROTATE_THRESHOLD:
                    change_reason = "threshold_not_met"
                else:
                    change_reason = "confirm_not_met"

        if change_event:
            action, block_reason = suggest_action(top, row_trend, row_mom)
            if action:
                prev_leader = top
            else:
                change_reason = "triggered_but_no_donor"

        decisions.append(
            {
                "date": dt,
                "signal_leader": top,
                "prev_leader": prev_leader_before,
                "held_leader": prev_leader,
                "rotate_diff": rotate_diff,
                "change_event": change_event,
                "change_reason": change_reason,
                "confirm_ok": confirm_ok,
                "action": action,
                "block_reason": block_reason,
                "candidates": candidates,
                "trend": row_trend,
                "momentum": row_mom,
            }
        )

        prev_top = top

    return decisions


def format_pct(value):
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value * 100:.2f}%"


def rebased_window(monthly, months):
    prices = monthly[TICKERS].copy()
    if months:
        prices = prices.tail(months)
    prices = prices.dropna(how="any")
    if prices.empty:
        return prices, None
    base = prices.iloc[0]
    return prices.divide(base) * 100, base


def build_plot_meta(decisions):
    rows = []
    for item in decisions:
        top = item["signal_leader"]
        prev = item["prev_leader"]
        diff = None
        if top is not None and prev is not None:
            mom = item["momentum"]
            if pd.notna(mom[top]) and pd.notna(mom[prev]):
                diff = mom[top] - mom[prev]
        rows.append(
            {
                "date": item["date"],
                "leader": top,
                "diff": diff,
                "change_event": item["change_event"],
            }
        )
    return pd.DataFrame(rows).set_index("date")


def save_visualization(monthly, sma10, trend_on, decisions, output_path, leader, change_event):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_n, base = rebased_window(monthly, REBASE_MONTHS)
    if data_n.empty or base is None:
        raise RuntimeError("Not enough overlapping data to rebase.")

    sma_window = sma10.loc[data_n.index, TICKERS]
    sma_n = sma_window.divide(base) * 100
    meta = build_plot_meta(decisions).reindex(data_n.index)

    fig, (ax_main, ax_aux) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    palette = {
        "QQQM": "#1f77b4",
        "EEM": "#ff7f0e",
        "XLE": "#2ca02c",
    }
    for dt, leader_month in meta["leader"].items():
        if pd.isna(leader_month):
            continue
        color = palette.get(leader_month, "#999999")
        start = dt.to_period("M").start_time
        end = dt.to_period("M").end_time
        ax_main.axvspan(start, end, color=color, alpha=0.08, lw=0)

    for idx, t in enumerate(TICKERS):
        ax_main.plot(
            data_n.index,
            data_n[t],
            label=t,
            color=palette.get(t, "#333333"),
            linewidth=1.5,
        )
        ax_main.plot(
            sma_n.index,
            sma_n[t],
            color=palette.get(t, "#333333"),
            linestyle="--",
            linewidth=1.0,
            alpha=0.7,
        )
        trend_series = trend_on.loc[data_n.index, t].where(sma_window[t].notna())
        on_mask = trend_series == True
        off_mask = trend_series == False
        ax_main.scatter(
            data_n.index[on_mask],
            data_n[t][on_mask],
            color="#2ca02c",
            s=12,
            label="Trend ON" if idx == 0 else None,
            zorder=4,
        )
        ax_main.scatter(
            data_n.index[off_mask],
            data_n[t][off_mask],
            color="#d62728",
            s=12,
            label="Trend OFF" if idx == 0 else None,
            zorder=4,
        )

    title_months = f"last {len(data_n)} months" if REBASE_MONTHS else "full history"
    ax_main.set_title(f"Rebased performance + SMA10 ({title_months})")
    leader_text = f"Leader: {leader}" if leader else "Leader: none"
    trigger_text = "Trigger: yes" if change_event else "Trigger: no"
    ax_main.text(
        0.01,
        0.98,
        f"{leader_text}\n{trigger_text}",
        transform=ax_main.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        color="#333333",
    )
    ax_main.text(
        0.99,
        0.02,
        "Dashed line = SMA10",
        transform=ax_main.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#666666",
    )
    ax_main.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    ax_main.legend(ncol=3, frameon=False)

    diff_series = pd.to_numeric(meta["diff"], errors="coerce") * 100
    ax_aux.plot(
        diff_series.index,
        diff_series,
        color="#333333",
        linewidth=1.2,
        label=f"Mom{MOMENTUM_MONTHS}m(top) - Mom{MOMENTUM_MONTHS}m(prev)",
    )
    ax_aux.axhline(
        ROTATE_THRESHOLD * 100,
        color="#d62728",
        linestyle="--",
        linewidth=1.0,
        label="3% threshold",
    )
    ax_aux.axhline(0, color="#999999", linewidth=0.6)
    trigger_mask = (meta["change_event"] == True) & diff_series.notna()
    ax_aux.scatter(
        diff_series.index[trigger_mask],
        diff_series[trigger_mask],
        color="#d62728",
        s=20,
        zorder=3,
        label="Change event",
    )
    ax_aux.set_ylabel("Momentum gap (%)")
    ax_aux.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    ax_aux.legend(ncol=3, frameon=False)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)



def main():
    try:
        monthly = fetch_month_end_prices(TICKERS)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    min_months = max(10, MOMENTUM_MONTHS + 1)
    if len(monthly) < min_months:
        print(
            f"Not enough monthly data to compute SMA10 and {MOMENTUM_MONTHS}m momentum."
        )
        return 1

    _sma10, trend_on, momentum12 = compute_indicators(monthly)
    decisions = simulate(monthly, trend_on, momentum12)
    if not decisions:
        print("Not enough data to compute signals yet.")
        return 1

    latest = decisions[-1]
    date = latest["date"].strftime("%Y-%m-%d")

    print("QQQM / EEM / XLE monthly rotation (month-end only)")
    print(f"As-of month-end: {date}")
    print("")
    print(f"Trend and {MOMENTUM_MONTHS}m momentum:")
    for ticker in TICKERS:
        trend_val = latest["trend"][ticker]
        if pd.isna(trend_val):
            trend_state = "NA"
        else:
            trend_state = "ON" if trend_val else "OFF"
        print(
            f"- {ticker}: trend {trend_state}, momentum {format_pct(latest['momentum'][ticker])}"
        )

    print("")
    signal_leader = latest["signal_leader"]
    if signal_leader is None:
        trend_on_any = any(
            pd.notna(latest["trend"][t]) and bool(latest["trend"][t])
            for t in TICKERS
        )
        if trend_on_any:
            print("Signal leader: none (momentum unavailable)")
        else:
            print("Signal leader: none (no trend ON)")
    else:
        print(f"Signal leader: {signal_leader}")

    if latest["prev_leader"] is None:
        print("Previous leader: none (initial)")
    else:
        print(f"Previous leader: {latest['prev_leader']}")

    print("")
    if latest["change_event"]:
        diff_text = format_pct(latest["rotate_diff"])
        print(f"Change event: true (top - prev_leader = {diff_text})")
    else:
        print("Change event: false")

    if latest["action"] is None:
        if latest["change_event"]:
            reason = latest["block_reason"] or "no donor"
            print(f"Action: hold ({reason})")
        else:
            print("Action: hold")
    else:
        amt_text = format_pct(latest["action"]["amount"])
        print(
            f"Action: sell {latest['action']['from']} {amt_text}, "
            f"buy {latest['action']['to']} {amt_text}"
        )
        print(
            f"Bounds check: ensure donor >= {FLOOR * 100:.0f}% and leader <= {CAP * 100:.0f}%"
        )

    output_path = Path(__file__).resolve().parent / "output" / "monthly_dashboard.png"
    try:
        save_visualization(
            monthly,
            _sma10,
            trend_on,
            decisions,
            output_path,
            latest["signal_leader"],
            latest["change_event"],
        )
        print(f"Chart saved: {output_path}")

    except (ImportError, RuntimeError) as exc:
        print(f"Chart skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
