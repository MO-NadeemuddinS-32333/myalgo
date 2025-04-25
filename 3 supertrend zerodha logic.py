
from kiteconnect import KiteConnect
import os
import datetime as dt
import pandas as pd
import numpy as np
import time
import warnings
from datetime import datetime, timedelta


cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")


#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)

instrument_df.to_excel('output.xlsx', index=False)


def instrumentLookup(instrument_df, symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol == symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker, interval, duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df, ticker)
    data = pd.DataFrame(kite.historical_data(
        instrument, dt.date.today()-dt.timedelta(duration), dt.date.today(), interval))
    data.set_index("date", inplace=True)
    return data


def atr_sma(df, period):
    df = df.copy()
    df['H-L'] = abs(df['high'] - df['low'])
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(period).mean()
    return df['ATR']

def supertrend(df, period=7, multiplier=3):
    df = df.copy()
    df['ATR'] = atr_sma(df, period)
    df['HL2'] = (df['high'] + df['low']) / 2
    df['UpperBand'] = df['HL2'] + (multiplier * df['ATR'])
    df['LowerBand'] = df['HL2'] - (multiplier * df['ATR'])

    df['UpperBand'] = df['UpperBand'].round(2)
    df['LowerBand'] = df['LowerBand'].round(2)

    df['Supertrend'] = np.nan
    df['InUptrend'] = True  # Start with uptrend

    for current in range(1, len(df)):
        previous = current - 1

        # Carry forward the trend
        if df['close'][current] > df['UpperBand'][previous]:
            df.loc[df.index[current], 'InUptrend'] = True
        elif df['close'][current] < df['LowerBand'][previous]:
            df.loc[df.index[current], 'InUptrend'] = False
        else:
            df.loc[df.index[current], 'InUptrend'] = df['InUptrend'][previous]

            # Adjust bands if needed
            if df['InUptrend'][current] and df['LowerBand'][current] < df['LowerBand'][previous]:
                df.loc[df.index[current], 'LowerBand'] = df['LowerBand'][previous]

            if not df['InUptrend'][current] and df['UpperBand'][current] > df['UpperBand'][previous]:
                df.loc[df.index[current], 'UpperBand'] = df['UpperBand'][previous]

        # Assign Supertrend value
        if df['InUptrend'][current]:
            df.loc[df.index[current], 'Supertrend'] = df['LowerBand'][current]
        else:
            df.loc[df.index[current], 'Supertrend'] = df['UpperBand'][current]

    return df['Supertrend']



def st_dir_refresh(ohlc, ticker):
    """function to check for supertrend reversal"""
    global st_dir
    if ohlc["st1"][-1] > ohlc["close"][-1] and ohlc["st1"][-2] < ohlc["close"][-2]:
        st_dir[ticker][0] = "red"
    if ohlc["st2"][-1] > ohlc["close"][-1] and ohlc["st2"][-2] < ohlc["close"][-2]:
        st_dir[ticker][1] = "red"
    if ohlc["st3"][-1] > ohlc["close"][-1] and ohlc["st3"][-2] < ohlc["close"][-2]:
        st_dir[ticker][2] = "red"
    if ohlc["st1"][-1] < ohlc["close"][-1] and ohlc["st1"][-2] > ohlc["close"][-2]:
        st_dir[ticker][0] = "green"
    if ohlc["st2"][-1] < ohlc["close"][-1] and ohlc["st2"][-2] > ohlc["close"][-2]:
        st_dir[ticker][1] = "green"
    if ohlc["st3"][-1] < ohlc["close"][-1] and ohlc["st3"][-2] > ohlc["close"][-2]:
        st_dir[ticker][2] = "green"


def sl_price(ohlc):
    """function to calculate stop loss based on supertrends"""
    st = ohlc.iloc[-1, [-3, -2, -1]]
    if st.min() > ohlc["close"][-1]:
        sl = (0.6*st.sort_values(ascending=True)
              [0]) + (0.4*st.sort_values(ascending=True)[1])
    elif st.max() < ohlc["close"][-1]:
        sl = (0.6*st.sort_values(ascending=False)
              [0]) + (0.4*st.sort_values(ascending=False)[1])
    else:
        sl = st.mean()
    return round(sl, 1)


def placeSLOrder(symbol, buy_sell, quantity, sl_price):
    # Place an intraday stop loss order on NSE
    if buy_sell == "buy":
        t_type = kite.TRANSACTION_TYPE_BUY
        t_type_sl = kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type = kite.TRANSACTION_TYPE_SELL
        t_type_sl = kite.TRANSACTION_TYPE_BUY
    kite.place_order(tradingsymbol=symbol,
                     exchange=kite.EXCHANGE_NSE,
                     transaction_type=t_type,
                     quantity=quantity,
                     order_type=kite.ORDER_TYPE_MARKET,
                     product=kite.PRODUCT_MIS,
                     variety=kite.VARIETY_REGULAR)
    time.sleep(0.2)  # 200 milliseconds
    kite.place_order(tradingsymbol=symbol,
                     exchange=kite.EXCHANGE_NSE,
                     transaction_type=t_type_sl,
                     quantity=quantity,
                     order_type=kite.ORDER_TYPE_SL,
                     price=sl_price,
                     trigger_price=sl_price,
                     product=kite.PRODUCT_MIS,
                     variety=kite.VARIETY_REGULAR)


def ModifyOrder(order_id, price):
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                      price=price,
                      trigger_price=price,
                      order_type=kite.ORDER_TYPE_SL,
                      variety=kite.VARIETY_REGULAR)


def main(capital):
    a, b = 0, 0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["day"])
            break
        except:
            print("can't extract position data..retrying")
            a += 1
    while b < 10:
        try:
            ord_df = pd.DataFrame(kite.orders())
            break
        except:
            print("can't extract order data..retrying")
            b += 1

    for ticker in tickers:
        print("========================================================================")
        print("starting passthrough for.....", ticker)
        try:
            ohlc = fetchOHLC(ticker, "5minute", 4)
            ohlc["st1"] = supertrend(ohlc, 7, 3)
            # print(ticker, "str 1 =", ohlc["st1"])
            ohlc["st2"] = supertrend(ohlc, 10, 3)
            # print(ticker, "str 2 =", ohlc["st2"])
            ohlc["st3"] = supertrend(ohlc, 11, 2)
            # print(ticker, "str 3 =", ohlc["st3"])
            st_dir_refresh(ohlc, ticker)
            quantity = int(capital/ohlc["close"][-1])
            if len(pos_df.columns) == 0:
                if st_dir[ticker] == ["green", "green", "green"]:
                    placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                if st_dir[ticker] == ["red", "red", "red"]:
                    placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
            if len(pos_df.columns) != 0 and ticker not in pos_df["tradingsymbol"].tolist():
                if st_dir[ticker] == ["green", "green", "green"]:
                    placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                if st_dir[ticker] == ["red", "red", "red"]:
                    placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
            if len(pos_df.columns) != 0 and ticker in pos_df["tradingsymbol"].tolist():
                if pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] == 0:
                    if st_dir[ticker] == ["green", "green", "green"]:
                        placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                    if st_dir[ticker] == ["red", "red", "red"]:
                        placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
                if pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] != 0:
                    order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (
                        ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].values[0]
                    ModifyOrder(order_id, sl_price(ohlc))
        # except:
        except Exception as e:
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("API error for ticker :", ticker)
            print("Exception message:", str(e), ticker)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")


#############################################################################################################
#############################################################################################################

tickers = ["SAMHI","NEWGEN","MMTC","WHIRLPOOL","SONACOMS","VIPIND","NATCOPHARM","THANGAMAYL","VAIBHAVGBL","MARKSANS","ELECTCAST","SHILPAMED","BAJAJHIND","TRIVENI","THERMAX","SYNGENE","WAAREEENER","CANFINHOME","NAVA","KFINTECH","RALLIS"]

#tickers to track - recommended to use max movers from previous day
capital = 30000 #position size
st_dir = {} #directory to store super trend status for each ticker
for ticker in tickers:
    st_dir[ticker] = ["None","None","None"]    
    
    
# Suppress FutureWarnings globally
warnings.simplefilter(action='ignore', category=FutureWarning)
    


#############################################################################################################
#############################################################################################################


# Wait until 9:15 AM
now = datetime.now()
target_time = now.replace(hour=13, minute=30, second=00, microsecond=0)

# If it's already past 9:15 AM today, wait until 9:15 AM the next day
if now > target_time:
    target_time += timedelta(days=1)

wait_seconds = (target_time - now).total_seconds()
print(f"Waiting until {target_time.strftime('%H:%M:%S')} to start...")
time.sleep(wait_seconds)

# Start loop at 9:15 AM
starttime = time.time()
timeout = time.time() + 60 * 60 * 7  # 6 hours

while time.time() <= timeout:
    try:
        main(capital)
        time.sleep(300 - ((time.time() - starttime) % 300.0))  # Run every 5 minutes
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()



