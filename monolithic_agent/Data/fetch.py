# Simple script to fetch EURUSD 1h data using tvdatafeed (no login)
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

# No username/password needed for public data
# EURUSD is a Forex symbol, so exchange is 'FX'
tv = TvDatafeed()

data = tv.get_hist(
    symbol='EURUSD',
    exchange='FX',
    interval=Interval.in_1_hour,
    n_bars=4000
)

# Save to CSV for inspection
output_file = 'data/eurusd_1h.csv'
data.to_csv(output_file)
print(f"Fetched {len(data)} bars. Saved to {output_file}")
