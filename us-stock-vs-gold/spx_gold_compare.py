#!/usr/bin/env python3
"""
Compare monthly DCA performance of SPY vs GLD and visualize in USD and gold terms.
"""

import argparse
from pathlib import Path
from typing import List, Tuple

try:
    import pandas as pd
    import yfinance as yf
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:
    name = getattr(exc, "name", "dependency")
    raise SystemExit(
        f"Missing dependency: {name}. Install with: pip install pandas yfinance matplotlib"
    ) from exc


GLD_INCEPTION = pd.Timestamp("2004-11-18")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare SPY vs GLD with monthly DCA and gold-denominated ratio."
    )
    parser.add_argument(
        "--contribution",
        type=float,
        default=1000.0,
        help="Monthly contribution in USD (default: 1000).",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=20,
        help="Lookback window in years when --start is not provided (default: 20).",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date override (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date override (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/spx_gold_comparison.png",
        help="Output image path (default: output/spx_gold_comparison.png).",
    )
    return parser.parse_args()


def resolve_dates(args: argparse.Namespace) -> Tuple[pd.Timestamp, pd.Timestamp]:
    end = pd.Timestamp(args.end) if args.end else pd.Timestamp.today().normalize()
    if args.start:
        start = pd.Timestamp(args.start)
    else:
        start = end - pd.DateOffset(years=args.years)
    if start < GLD_INCEPTION:
        start = GLD_INCEPTION
    if start > end:
        raise SystemExit("Start date must be before end date.")
    return start, end


def fetch_monthly_adj_close(
    tickers: List[str], start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    data = yf.download(
        tickers=tickers,
        start=start.strftime("%Y-%m-%d"),
        end=(end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        actions=False,
        progress=False,
    )
    if "Adj Close" not in data.columns:
        raise SystemExit("Expected 'Adj Close' in yfinance output.")
    adj = data["Adj Close"]
    if isinstance(adj, pd.Series):
        adj = adj.to_frame()
    adj = adj.rename(columns={col: str(col).upper() for col in adj.columns})
    if getattr(adj.index, "tz", None) is not None:
        adj.index = adj.index.tz_localize(None)
    monthly = adj.resample("M").last().dropna()
    return monthly


def dca_units_and_values(
    prices: pd.DataFrame, contribution: float
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    units = (contribution / prices).cumsum()
    values = units * prices
    return units, values


def main() -> None:
    args = parse_args()
    start, end = resolve_dates(args)
    monthly = fetch_monthly_adj_close(["SPY", "GLD"], start, end)

    if monthly.empty:
        raise SystemExit("No data returned for the selected date range.")

    units, values = dca_units_and_values(monthly, args.contribution)
    spy_value = values["SPY"]
    gld_units = units["GLD"]
    gld_price = monthly["GLD"]

    spy_in_gld_units = spy_value / gld_price
    ratio = spy_in_gld_units / gld_units

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax1.plot(values.index, values["SPY"], label="SPY DCA value (USD)", color="tab:blue")
    ax1.plot(values.index, values["GLD"], label="GLD DCA value (USD)", color="tab:orange")
    ax1.set_ylabel("Portfolio value (USD)")
    ax1.set_title("Monthly DCA portfolio value")
    ax1.grid(alpha=0.2)
    ax1.legend()

    ax2.plot(
        ratio.index,
        ratio,
        label="SPY value in GLD units / GLD units held",
        color="tab:green",
    )
    ax2.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax2.set_ylabel("Ratio (baseline = 1)")
    ax2.set_title("Gold-denominated comparison")
    ax2.grid(alpha=0.2)
    ax2.legend()

    fig.suptitle(f"SPY vs GLD monthly DCA (${args.contribution:,.0f})")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=150)

    total_contrib = args.contribution * len(monthly)
    print(f"Date range: {monthly.index[0].date()} to {monthly.index[-1].date()}")
    print(f"Total contributions: ${total_contrib:,.2f}")
    print(f"Final SPY value: ${spy_value.iloc[-1]:,.2f}")
    print(f"Final GLD value: ${values['GLD'].iloc[-1]:,.2f}")
    print(f"Final SPY value in GLD units: {spy_in_gld_units.iloc[-1]:,.4f}")
    print(f"Final GLD units held: {gld_units.iloc[-1]:,.4f}")
    print(f"Final ratio (SPY in GLD / GLD units): {ratio.iloc[-1]:,.4f}")
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    main()
