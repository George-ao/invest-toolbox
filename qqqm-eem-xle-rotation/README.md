# QQQM / EEM / XLE Monthly Rotation Tool

This tool implements the monthly, month-end-only strategy you specified:
- SMA10 trend filter on month-end prices only
- 6-month momentum for ranking among trend-ON ETFs
- Default hold when there is no change event (no forced risk-off)
- Change event when signal leader changes and momentum gap vs previous leader >= 3%
- On change event, move a small fixed step from the weakest ETF
  (lowest momentum, with trend OFF prioritized) to the new leader

Data source:
- Yahoo Finance via `yfinance` with `auto_adjust=True`
- Month-end prices are derived from daily data by taking the last trading day

Requirements:
- Python 3
- `pip install yfinance pandas matplotlib`

Run:
```
python rotation_tool.py
```

Visualization:
- The script saves a chart to `qqqm-eem-xle-rotation/output/monthly_dashboard.png`.
- The main panel shows rebased performance (start=100) plus SMA10 (dashed) with
  trend ON/OFF markers and a light leader background band.
- The lower panel shows `mom6m(top) - mom6m(prev_leader)` with the 3% threshold and
  change-event markers.

Key parameters (edit in `rotation_tool.py`):
- `DELTA`: step size per change event (default 10%)
- `FLOOR`: minimum allocation per ETF (default 10%)
- `CAP`: maximum allocation per ETF (default 60%)
- `REQUIRE_TWO_MONTH_CONFIRMATION`: optional extra filter before a change event

Notes:
- The script does not use your current holdings; it outputs a suggested action.
- Apply floor/cap checks against your actual portfolio before trading.
