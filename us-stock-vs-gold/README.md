# US Stock vs Gold (SPY vs GLD)

![SPY vs GLD DCA](output/spx_gold_comparison.png)

Compares monthly DCA performance between `SPY` and `GLD` and outputs a chart.

## User case

You invest every month and want to see whether US stocks or gold performed better over a long window.

```bash
python spx_gold_compare.py
```

## Output

- `output/spx_gold_comparison.png`

## Run

```bash
pip install pandas yfinance matplotlib
python spx_gold_compare.py
```

For full options, use:

```bash
python spx_gold_compare.py --help
```
