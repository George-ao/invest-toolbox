# SPX vs gold visual validation plan

## Goal
- Compare the last 20 years of US equities growth in USD and in gold terms.
- Determine whether SPX grows in gold terms.
- Use a DCA strategy with dividends reinvested; compare against equal-cash DCA into gold.
- Produce a single figure (possibly 2-panel) that communicates both comparisons.

## Data source (chosen)
- Provider: Yahoo Finance via `yfinance` (no API key, full daily history, widely used).
- Equity proxy: `SPY` adjusted close (most liquid S&P 500 ETF; adj close reflects splits and dividend reinvestment for total-return style series).
- Gold proxy: `GLD` adjusted close (most liquid gold ETF; tracks spot gold net of fees).
Notes: ETF proxies introduce tracking/fee bias, but provide the cleanest, most complete 20-year dataset with high liquidity.
Decision: use investment proxies (`SPY` vs `GLD`), not spot gold.

## Baseline / normalization
- DCA baseline: fixed monthly contribution ($1000) to both SPY and GLD.
- Ratio baseline: 1.0 means SPY DCA value equals GLD DCA value when expressed in GLD units.

## Calculations
- Window: last 20 years from today, but clamp to GLD inception date (2004-11-18) if earlier.
- Start date rule: `start_date = max(today - 20y, 2004-11-18)`.
- SPX total return in USD: use adjusted close for SPY or total return index.
- Gold price in USD: use GLD adjusted close.
- DCA simulation (monthly, $1000):
  - Add contribution at month-end.
  - Buy shares/oz at month-end price.
  - Track portfolio value in USD each month.
- Gold-denominated comparison:
  - Convert SPY portfolio value into GLD units: `V_spy_usd / P_gld`.
  - Compare against GLD units accumulated via DCA.
  - Ratio line: `(V_spy_usd / P_gld) / gld_units` (baseline = 1).

## Visualization
- Single image with two panels for readability (linear scale):
  1) DCA portfolio value in USD: SPY vs GLD (equal monthly contributions).
  2) Gold-denominated comparison: ratio line with baseline at 1.

## Output
- Save image to `output/spx_gold_comparison.png` (path configurable).
- Script outputs a small summary table to stdout.

## Confirmed choices
- Data source: Yahoo Finance via `yfinance` with `SPY` and `GLD`.
- DCA frequency: monthly.
- Start date: last 20 years, clamped to GLD inception date.
- Visualization: two-panel figure.
