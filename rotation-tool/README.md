# Monthly Rotation Tool

Generates month-end rotation signals for an ETF set and saves a dashboard chart.

## User case

You review a small ETF basket once per month and want a clear rotation signal.

```bash
python rotation_tool.py
```

You want to run the same logic on your own ETF basket.

```bash
python rotation_tool.py --tickers QQQ IWM XLK
```

## Output

- `output/monthly_dashboard.png`

## Run

```bash
pip install pandas yfinance matplotlib
python rotation_tool.py
```

For full options, use:

```bash
python rotation_tool.py --help
```
