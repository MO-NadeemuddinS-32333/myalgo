#pip install pyotp
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from pyotp import TOTP
import tempfile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import warnings
import threading
import concurrent.futures  # Import concurrent futures for threading
from datetime import datetime, timedelta
import datetime as dt
import pandas as pd
import numpy as np

cwd = os.getcwd()

def autologin():


        token_path = os.path.join(cwd,'api_key.txt')
        key_secret = open(token_path,'r').read().split()
        kite = KiteConnect(api_key=key_secret[0])

        temp_profile = tempfile.mkdtemp()
        
        
        #Set up Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

        #Start Chrome service
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        
        
        driver.get(kite.login_url())
        driver.implicitly_wait(10)
        username = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
        password = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
        username.send_keys(key_secret[2])
        password.send_keys(key_secret[3])
        driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
        totp = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input')
        #totp_token = TOTP(key_secret[4])
        totp_token = TOTP("3MPQTCB4OQHQOGQPPAXHX3MGDZPFSASP")
        token = totp_token.now()
        print(token)
        totp.send_keys(token)
        time.sleep(10)
        request_token=driver.current_url.split('request_token=')[1][:32]
        print("********************************************************")
        print(request_token)
        print("********************************************************")
        with open(os.path.join(cwd,'request_token.txt'), 'w') as the_file:
            the_file.write(request_token)
        driver.quit()

autologin()



#generating and storing access token - valid till 6 am the next day
request_token = open(os.path.join(cwd,'request_token.txt'),'r').read()
key_secret = open(os.path.join(cwd,'api_key.txt'),'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
data = kite.generate_session(request_token, api_secret=key_secret[1])
with open(os.path.join('access_token.txt'), 'w') as file:
    file.write(data["access_token"])
    
    
    

# Get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)


def instrumentLookup(instrument_df, symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol == symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker, interval, duration):
    """Extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df, ticker)
    data = pd.DataFrame(kite.historical_data(instrument, dt.date.today() - dt.timedelta(duration), dt.date.today(), interval))
    data.set_index("date", inplace=True)
    return data


def atr(DF, n):
    "Function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L'] = abs(df['high'] - df['low'])
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
    df['ATR'] = df['TR'].ewm(com=n, min_periods=n).mean()
    return df['ATR']


def supertrend(DF, n, m):
    """Function to calculate Supertrend given historical candle data"""
    df = DF.copy()
    df['ATR'] = atr(df, n)
    df["B-U"] = ((df['high'] + df['low']) / 2) + m * df['ATR']
    df["B-L"] = ((df['high'] + df['low']) / 2) - m * df['ATR']
    df["U-B"] = df["B-U"]
    df["L-B"] = df["B-L"]
    ind = df.index
    for i in range(n, len(df)):
        if df['close'][i-1] <= df['U-B'][i-1]:
            df.loc[ind[i], 'U-B'] = min(df['B-U'][i], df['U-B'][i-1])
        else:
            df.loc[ind[i], 'U-B'] = df['B-U'][i]
    for i in range(n, len(df)):
        if df['close'][i-1] >= df['L-B'][i-1]:
            df.loc[ind[i], 'L-B'] = max(df['B-L'][i], df['L-B'][i-1])
        else:
            df.loc[ind[i], 'L-B'] = df['B-L'][i]
    df['Strend'] = np.nan
    for test in range(n, len(df)):
        if df['close'][test-1] <= df['U-B'][test-1] and df['close'][test] > df['U-B'][test]:
            df.loc[ind[test], 'Strend'] = df['L-B'][test]
            break
        if df['close'][test-1] >= df['L-B'][test-1] and df['close'][test] < df['L-B'][test]:
            df.loc[ind[test], 'Strend'] = df['U-B'][test]
            break
    for i in range(test+1, len(df)):
        if df['Strend'][i-1] == df['U-B'][i-1] and df['close'][i] <= df['U-B'][i]:
            df.loc[ind[i], 'Strend'] = df['U-B'][i]
        elif df['Strend'][i-1] == df['U-B'][i-1] and df['close'][i] >= df['U-B'][i]:
            df.loc[ind[i], 'Strend'] = df['L-B'][i]
        elif df['Strend'][i-1] == df['L-B'][i-1] and df['close'][i] >= df['L-B'][i]:
            df.loc[ind[i], 'Strend'] = df['L-B'][i]
        elif df['Strend'][i-1] == df['L-B'][i-1] and df['close'][i] <= df['L-B'][i]:
            df.loc[ind[i], 'Strend'] = df['U-B'][i]
    return df['Strend']

# Create a Lock object
lock = threading.Lock()


def st_dir_refresh(ohlc, ticker):
    """Function to check for supertrend reversal"""
    
    global st_dir
    
    
    with lock:
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
    """Function to calculate stop loss based on supertrends"""
    st = ohlc.iloc[-1, [-3, -2, -1]]
    if st.min() > ohlc["close"][-1]:
        sl = (0.6 * st.sort_values(ascending=True)[0]) + (0.4 * st.sort_values(ascending=True)[1])
    elif st.max() < ohlc["close"][-1]:
        sl = (0.6 * st.sort_values(ascending=False)[0]) + (0.4 * st.sort_values(ascending=False)[1])
    else:
        sl = st.mean()
    return round(sl, 1)


def placeSLOrder(symbol, buy_sell, quantity, sl_price):
    """Place an intraday stop loss order on NSE"""
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
    time.sleep(0.5)
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
    """Modify order given order id"""
    kite.modify_order(order_id=order_id,
                      price=price,
                      trigger_price=price,
                      order_type=kite.ORDER_TYPE_SL,
                      variety=kite.VARIETY_REGULAR)


def process_ticker(ticker, capital, pos_df, ord_df):
    """Process individual ticker"""
    print("========================================================================")
    print("Starting passthrough for.....", ticker)
    try:
        ohlc = fetchOHLC(ticker, "5minute", 4)
        ohlc["st1"] = supertrend(ohlc, 7, 3)
        #print(ticker, "str 1 =", ohlc["st1"])
        ohlc["st2"] = supertrend(ohlc, 10, 3)
        #print(ticker, "str 2 =", ohlc["st2"])
        ohlc["st3"] = supertrend(ohlc, 11, 2)
        #print(ticker, "str 3 =", ohlc["st3"])
        st_dir_refresh(ohlc, ticker)
        quantity = int(capital / ohlc["close"][-1])
        if len(pos_df.columns) == 0:
            if st_dir[ticker] == ["green", "green", "green"]:
                placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                print("order placed successfully",ticker)
            if st_dir[ticker] == ["red", "red", "red"]:
                placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
                print("order placed successfully",ticker)
        if len(pos_df.columns) != 0 and ticker not in pos_df["tradingsymbol"].tolist():
            if st_dir[ticker] == ["green", "green", "green"]:
                placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                print("order placed successfully",ticker)
            if st_dir[ticker] == ["red", "red", "red"]:
                placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
                print("order placed successfully",ticker)
        if len(pos_df.columns) != 0 and ticker in pos_df["tradingsymbol"].tolist():
            if pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] == 0:
                if st_dir[ticker] == ["green", "green", "green"]:
                    placeSLOrder(ticker, "buy", quantity, sl_price(ohlc))
                    print("order placed successfully",ticker)
                if st_dir[ticker] == ["red", "red", "red"]:
                    placeSLOrder(ticker, "sell", quantity, sl_price(ohlc))
                    print("order placed successfully",ticker)
            if pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] != 0:
                order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].values[0]
                ModifyOrder(order_id, sl_price(ohlc))
                print("order modified successfully",ticker)
    except Exception as e:
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("API error for ticker :", ticker)
        print("Exception message:", str(e), ticker)
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")


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
    
    # Use ThreadPoolExecutor to handle multithreading for each ticker
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for all tickers
        futures = [executor.submit(process_ticker, ticker, capital, pos_df, ord_df) for ticker in tickers]
        # Wait for all futures to complete
        concurrent.futures.wait(futures)



tickers = ["RBLBANK","DCBBANK","PARAS","GRSE","MIDHANI","SONATSOFTW","DATAPATTNS","COCHINSHIP","PARADEEP","CAPLIPOINT","TEJASNET","LLOYDSENGG","SHRIRAMFIN","WEBELSOLAR","RKFORGE","CHOLAHLDNG","EQUITASBNK"]


# Tickers to track
capital = 30000  # Position size
st_dir = {}  # Directory to store supertrend status for each ticker
for ticker in tickers:
    st_dir[ticker] = ["None", "None", "None"]

# Suppress FutureWarnings globally
warnings.simplefilter(action='ignore', category=FutureWarning)



#################################################################################
starttime=time.time()
timeout = time.time() + 60*60*6  # 60 seconds times 360 meaning 6 hrs
while time.time() <= timeout:
    try:
        main(capital)
        time.sleep(300 - ((time.time() - starttime) % 300.0))

    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()      