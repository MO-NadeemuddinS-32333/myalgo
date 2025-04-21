# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 21:36:50 2025

@author: USER
"""
#pip install ta
from kiteconnect import KiteConnect, KiteTicker
import pandas as pd
import datetime
import time
import ta
#from zerodha_login import kite

# Get instrument token for ADANIENT
instruments = kite.instruments()
df_instruments = pd.DataFrame(instruments)
token = df_instruments[df_instruments.tradingsymbol == "NIFTYBEES"]["instrument_token"].values[0]

# Get OHLC data for 5 years
from_date = datetime.datetime.now() - datetime.timedelta(days=365 * 5)
to_date = datetime.datetime.now()
interval = "5minute"

def fetch_5_years_data(token):
    df_final = pd.DataFrame()
    start = from_date
    while start < to_date:
        end = min(start + datetime.timedelta(days=100), to_date)
        data = kite.historical_data(token, start, end, interval)
        df = pd.DataFrame(data)
        df_final = pd.concat([df_final, df])
        start = end
        time.sleep(1)  # to avoid rate limits
    return df_final.reset_index(drop=True)

data = fetch_5_years_data(token)


def compute_supertrend(df, period=7, multiplier=3):
    high = df['high']
    low = df['low']
    close = df['close']
    atr = ta.volatility.average_true_range(high, low, close, window=period)
    hl2 = (high + low) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    supertrend = [True] * len(df)
    for i in range(1, len(df)):
        curr_close = close.iloc[i]
        prev_close = close.iloc[i - 1]

        if curr_close > upperband.iloc[i - 1]:
            supertrend[i] = True
        elif curr_close < lowerband.iloc[i - 1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i - 1]

            if supertrend[i] and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = lowerband.iloc[i - 1]

            if not supertrend[i] and upperband.iloc[i] > upperband.iloc[i - 1]:
                upperband.iloc[i] = upperband.iloc[i - 1]

    supertrend_df = pd.DataFrame({
        f'supertrend_{period}_{multiplier}': supertrend,
        f'upper_{period}_{multiplier}': upperband,
        f'lower_{period}_{multiplier}': lowerband
    })

    return supertrend_df


# Compute all 3 Supertrends
st1 = compute_supertrend(data, period=7, multiplier=3)
st2 = compute_supertrend(data, period=10, multiplier=3)
st3 = compute_supertrend(data, period=11, multiplier=3)

data = pd.concat([data, st1, st2, st3], axis=1)

# Backtest loop
in_position = False
position_type = None
entry_price = 0
sl_price = 0
returns = []

for i in range(1, len(data)):
    row = data.iloc[i]

    # All three Supertrends in same direction
    buy_signal = row['supertrend_7_3'] and row['supertrend_10_3'] and row['supertrend_11_3']
    sell_signal = not row['supertrend_7_3'] and not row['supertrend_10_3'] and not row['supertrend_11_3']

    # Trailing SL between ST1 and ST2
    trailing_sl = (row['lower_7_3'] + row['lower_10_3']) / 2 if buy_signal else (row['upper_7_3'] + row['upper_10_3']) / 2

    if not in_position:
        if buy_signal:
            in_position = True
            position_type = "LONG"
            entry_price = row['close']
            sl_price = trailing_sl
        elif sell_signal:
            in_position = True
            position_type = "SHORT"
            entry_price = row['close']
            sl_price = trailing_sl

    elif in_position:
        # Update SL
        new_sl = trailing_sl

        if position_type == "LONG":
            if row['close'] < new_sl:
                returns.append((row['close'] - entry_price) / entry_price)
                in_position = False
            else:
                sl_price = max(sl_price, new_sl)

        elif position_type == "SHORT":
            if row['close'] > new_sl:
                returns.append((entry_price - row['close']) / entry_price)
                in_position = False
            else:
                sl_price = min(sl_price, new_sl)

# Final performance
import numpy as np
total_return = np.sum(returns)
print(f"Total Return over 5 years: {total_return * 100:.2f}%")