# Invest Toolbox

A small collection of ETF analysis tools.

## Tools

1. `qqqm-eem-xle-rotation/rotation_tool.py`
   Monthly rotation signal tool for ETF sets (default: `QQQM EEM XLE`).
2. `us-stock-vs-gold/spx_gold_compare.py`
   Monthly DCA comparison tool for `SPY` vs `GLD`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas yfinance matplotlib
```

## User cases

1. You want a monthly rotation signal and dashboard for `QQQM`, `EEM`, `XLE`.
2. You want to compare long-term monthly DCA performance between US stocks and gold.

## Run

```bash
python qqqm-eem-xle-rotation/rotation_tool.py
python us-stock-vs-gold/spx_gold_compare.py
```
