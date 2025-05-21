# -*- coding: utf-8 -*-
"""
Zerodha Kite Connect - Supertrend Strategy

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""
from kiteconnect import KiteConnect
import os
import datetime as dt
import pandas as pd
import numpy as np
import time
import warnings


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


def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']


def supertrend(DF,n,m):
    """function to calculate Supertrend given historical candle data
        n = n day ATR - usually 7 day ATR is used
        m = multiplier - usually 2 or 3 is used"""
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["B-U"]=((df['high']+df['low'])/2) + m*df['ATR'] 
    df["B-L"]=((df['high']+df['low'])/2) - m*df['ATR']
    df["U-B"]=df["B-U"]
    df["L-B"]=df["B-L"]
    ind = df.index
    for i in range(n,len(df)):
        if df['close'].iloc[i-1]<=df['U-B'].iloc[i-1]:
            df.loc[ind[i],'U-B']=min(df['B-U'].iloc[i],df['U-B'].iloc[i-1])
        else:
            df.loc[ind[i],'U-B']=df['B-U'].iloc[i]    
    for i in range(n,len(df)):
        if df['close'].iloc[i-1]>=df['L-B'].iloc[i-1]:
            df.loc[ind[i],'L-B']=max(df['B-L'].iloc[i],df['L-B'].iloc[i-1])
        else:
            df.loc[ind[i],'L-B']=df['B-L'].iloc[i]  
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['close'].iloc[test-1]<=df['U-B'].iloc[test-1] and df['close'].iloc[test]>df['U-B'].iloc[test]:
            df.loc[ind[test],'Strend']=df['L-B'].iloc[test]
            break
        if df['close'].iloc[test-1]>=df['L-B'].iloc[test-1] and df['close'].iloc[test]<df['L-B'].iloc[test]:
            df.loc[ind[test],'Strend']=df['U-B'].iloc[test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'].iloc[i-1]==df['U-B'].iloc[i-1] and df['close'].iloc[i]<=df['U-B'].iloc[i]:
            df.loc[ind[i],'Strend']=df['U-B'].iloc[i]
        elif  df['Strend'].iloc[i-1]==df['U-B'].iloc[i-1] and df['close'].iloc[i]>=df['U-B'].iloc[i]:
            df.loc[ind[i],'Strend']=df['L-B'].iloc[i]
        elif df['Strend'].iloc[i-1]==df['L-B'].iloc[i-1] and df['close'].iloc[i]>=df['L-B'].iloc[i]:
            df.loc[ind[i],'Strend']=df['L-B'].iloc[i]
        elif df['Strend'].iloc[i-1]==df['L-B'].iloc[i-1] and df['close'].iloc[i]<=df['L-B'].iloc[i]:
            df.loc[ind[i],'Strend']=df['U-B'].iloc[i]
    return df['Strend']


def st_dir_refresh(ohlc,ticker):
    """function to check for supertrend reversal"""
    global st_dir
    if ohlc["st1"].iloc[-1] > ohlc["close"].iloc[-1] and ohlc["st1"].iloc[-2] < ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[0] = "red"
    if ohlc["st2"].iloc[-1] > ohlc["close"].iloc[-1] and ohlc["st2"].iloc[-2] < ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[1] = "red"
    if ohlc["st3"].iloc[-1] > ohlc["close"].iloc[-1] and ohlc["st3"].iloc[-2] < ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[2] = "red"
    if ohlc["st1"].iloc[-1] < ohlc["close"].iloc[-1] and ohlc["st1"].iloc[-2] > ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[0] = "green"
    if ohlc["st2"].iloc[-1] < ohlc["close"].iloc[-1] and ohlc["st2"].iloc[-2] > ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[1] = "green"
    if ohlc["st3"].iloc[-1] < ohlc["close"].iloc[-1] and ohlc["st3"].iloc[-2] > ohlc["close"].iloc[-2]:
        st_dir[ticker].iloc[2] = "green"

def sl_price(ohlc, buffer=1.0):
    """Set SL 1x ATR below entry for buy, above for sell"""
    try:
        atr_val = ohlc['ATR'].iloc[-1]
        close = ohlc['close'].iloc[-1]
        in_uptrend = ohlc['in_uptrend'].iloc[-1]

        if in_uptrend:
            sl = close - (1.0 * atr_val) - buffer
        else:
            sl = close + (1.0 * atr_val) + buffer

        return round(sl, 1)
    except KeyError as e:
        print(f"Missing key in OHLC data: {e}")
        return None


def placeSLOrder(symbol,buy_sell,quantity,sl_price):    
    # Place an intraday stop loss order on NSE - handles market orders converted to limit orders
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
        t_type_sl=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
        t_type_sl=kite.TRANSACTION_TYPE_BUY
    market_order = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    a = 0
    while a < 10:
        try:
            order_list = kite.orders()
            break
        except:
            print("can't get orders..retrying")
            a+=1
    for order in order_list:
        if order["order_id"]==market_order:
            if order["status"]=="COMPLETE":
                kite.place_order(tradingsymbol=symbol,
                                exchange=kite.EXCHANGE_NSE,
                                transaction_type=t_type_sl,
                                quantity=quantity,
                                order_type=kite.ORDER_TYPE_SL,
                                price=sl_price,
                                trigger_price = sl_price,
                                product=kite.PRODUCT_MIS,
                                variety=kite.VARIETY_REGULAR)
            else:
                kite.cancel_order(order_id=market_order,variety=kite.VARIETY_REGULAR)


def ModifyOrder(order_id,price):    
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                    price=price,
                    trigger_price=price,
                    order_type=kite.ORDER_TYPE_SL,
                    variety=kite.VARIETY_REGULAR)      

def main(capital):
    a,b = 0,0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["day"])
            break
        except:
            print("can't extract position data..retrying")
            a+=1
    while b < 10:
        try:
            ord_df = pd.DataFrame(kite.orders())
            break
        except:
            print("can't extract order data..retrying")
            b+=1
    
    for ticker in tickers:
        print("_____________________________________________________________")
        print("starting passthrough for.....",ticker)
        try:
            ohlc = fetchOHLC(ticker,"5minute",4)
            ohlc["st1"] = supertrend(ohlc,11,2)
            ohlc["st2"] = supertrend(ohlc,11,2)
            ohlc["st3"] = supertrend(ohlc,11,2)
            st_dir_refresh(ohlc,ticker)
            quantity = int(capital/ohlc["close"].iloc[-1])
            if len(pos_df.columns)==0:
                if st_dir[ticker] == ["green","green","green"]:
                    print("order placed for", ticker)
                    placeSLOrder(ticker,"buy",quantity,sl_price(ohlc))
                if st_dir[ticker] == ["red","red","red"]:
                    print("order placed for", ticker)
                    placeSLOrder(ticker,"sell",quantity,sl_price(ohlc))
            if len(pos_df.columns)!=0 and ticker not in pos_df["tradingsymbol"].tolist():
                if st_dir[ticker] == ["green","green","green"]:
                    placeSLOrder(ticker,"buy",quantity,sl_price(ohlc))
                if st_dir[ticker] == ["red","red","red"]:
                    placeSLOrder(ticker,"sell",quantity,sl_price(ohlc))
            if len(pos_df.columns)!=0 and ticker in pos_df["tradingsymbol"].tolist():
                if pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] == 0:
                    if st_dir[ticker] == ["green","green","green"]:
                        placeSLOrder(ticker,"buy",quantity,sl_price(ohlc))
                    if st_dir[ticker] == ["red","red","red"]:
                        placeSLOrder(ticker,"sell",quantity,sl_price(ohlc))
                if pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] != 0:
                    order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING","OPEN"]))]["order_id"].values[0]
                    ModifyOrder(order_id,sl_price(ohlc))
        except Exception as e:
            print("****************************************************************")
            print("API error for ticker :",ticker)
            print("Exception message:", str(e), ticker)
            print("****************************************************************")
            
            
            
def get_pnl():
    try:
        # Get all orders - You can also filter by date or symbol
        orders = kite.orders()
        # Fetch all trades
        trades = kite.trades()
        
        # Calculate P&L (Profit and Loss)
        pnl = 0
        for trade in trades:
            pnl += trade['realized_profit']
        
        # Display the P&L
        print(f"Total Realized P&L: ₹{pnl}")
    
    except Exception as e:
        print(f"Error fetching P&L: {e}")
            
            
#############################################################################################################
#############################################################################################################
tickers = ['AARTIIND', 'LODHA', 'STYLEBAAZA', 'NIITMTS', 'SAILIFE', 'TIPSMUSIC', 'PANACEABIO', 'VMM', 'GUJGASLTD', 'HNGSNGBEES', 'ASAHIINDIA', 'MINDTECK', 'OMINFRAL', 'VBL', 'PNBHOUSING', 'CHAMBLFERT', 'CGCL', 'JSFB', 'SBFC', 'COFORGE', 'PGEL', 'JASH', 'PDSL', 'KAYNES', 'ORIENTELEC', 'PREMEXPLN', 'FOODSIN', 'GRAPHITE', 'SHK', 'NDTV', 'THEMISMED', 'APLLTD', 'ANUHPHR', 'KPEL', 'NUCLEUS', 'UDS', 'BHAGERIA', 'GOODLUCK', 'KIRLOSIND', 'SUVEN', 'PRECWIRE', 'GRINFRA', 'KPIGREEN', 'MODIRUBBER', 'AVANTEL', 'MAZDA', 'DELHIVERY', 'KANPRPLA', 'GILLANDERS', 'RPSGVENT', 'HINDWAREAP', 'INOXGREEN', '20MICRONS', 'SHANKARA', 'SIYSIL', 'DONEAR', 'REPRO', 'TIINDIA', 'GAIL', 'DABUR', 'TORNTPHARM', 'LAURUSLABS', 'VOLTAS', 'BIOCON', 'NTPC', 'HINDUNILVR', 'SUNPHARMA']

    
# Suppress FutureWarnings globally
warnings.simplefilter(action='ignore', category=FutureWarning)
    


#tickers to track - recommended to use max movers from previous day
capital = 30000 #position size

st_dir = {} #directory to store super trend status for each ticker
for ticker in tickers:
    st_dir[ticker] = ["None","None","None"]    

starttime=time.time()
timeout = time.time() + 60*60*6  # 60 seconds times 360 meaning 6 hrs
while time.time() <= timeout:
    try:
        main(capital)
        time.sleep(300 - ((time.time() - starttime) % 300.0))
        MTM = get_pnl()

    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()        



