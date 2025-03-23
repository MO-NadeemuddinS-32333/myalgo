# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 04:13:57 2025

@author: USER
"""
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import time
import numpy as np


api_key = "jyheto7j2tbcjutp"
api_secret = "o4wxe6qt7cnay0kd0ymybecevg0pnvgi"
kite = KiteConnect(api_key=api_key)
print(kite.login_url()) #use this url to manually login and authorize yourself

#generate trading session
request_token = "v2JV1ciKOn0D7m27PJhUG2ggdjM8Kpw1" #Extract request token from the redirect url obtained after you authorize yourself by loggin in
data = kite.generate_session(request_token, api_secret=api_secret)

#create kite trading object
kite.set_access_token(data["access_token"])


#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)



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

def doji(ohlc_df):    
    """returns dataframe with doji candle column"""
    df = ohlc_df.copy()
    avg_candle_size = abs(df["close"] - df["open"]).median()
    df["doji"] = abs(df["close"] - df["open"]) <=  (0.05 * avg_candle_size)
    return df

def maru_bozu(ohlc_df):
    """Returns dataframe with maru bozu candle column."""
    
    # Create a copy of the dataframe to avoid modifying the original
    df = ohlc_df.copy()
    
    # Calculate the average candle size
    avg_candle_size = abs(df["close"] - df["open"]).median()
    
    # Calculate required differences only once
    df["h_c"] = df["high"] - df["close"]
    df["l_o"] = df["low"] - df["open"]
    df["h_o"] = df["high"] - df["open"]
    df["l_c"] = df["low"] - df["close"]
    
    # Define conditions for maru bozu candles
    green_condition = (
        (df["close"] - df["open"] > 2 * avg_candle_size) &
        (df[["h_c", "l_o"]].max(axis=1) < 0.005 * avg_candle_size)
    )
    
    red_condition = (
        (df["open"] - df["close"] > 2 * avg_candle_size) &
        (df[["h_o", "l_c"]].max(axis=1) < 0.005 * avg_candle_size)
    )
    
    # Assign maru bozu candle types based on conditions
    df["maru_bozu"] = np.where(green_condition, "maru_bozu_green", 
                               np.where(red_condition, "maru_bozu_red", False))
    
    # Drop temporary columns
    df.drop(["h_c", "l_o", "h_o", "l_c"], axis=1, inplace=True)
    
    return df

def hammer(ohlc_df):
    """Returns dataframe with hammer candle column."""
    
    # Create a copy of the original DataFrame to avoid modifying it
    df = ohlc_df.copy()
    
    # Calculate the required values once and store them in variables
    high_low_diff = df["high"] - df["low"]
    open_close_diff = df["close"] - df["open"]
    close_low_diff = df["close"] - df["low"]
    open_low_diff = df["open"] - df["low"]
    
    # Define the conditions for a hammer candle
    is_long_body = open_close_diff.abs() > 0.1 * high_low_diff
    is_upper_shadow_small = close_low_diff / (np.maximum(high_low_diff, 0.001)) > 0.6
    is_lower_shadow_large = open_low_diff / (np.maximum(high_low_diff, 0.001)) > 0.6
    is_large_range = high_low_diff > 3 * open_close_diff
    
    # Combine the conditions for the hammer candle
    hammer_condition = is_long_body & is_upper_shadow_small & is_lower_shadow_large & is_large_range
    
    # Add a new column for the hammer condition
    df["hammer"] = hammer_condition
    
    return df



def shooting_star(ohlc_df):
    """Returns dataframe with shooting star candle column."""
    
    # Create a copy of the DataFrame to avoid modifying the original
    df = ohlc_df.copy()
    
    # Calculate the required values once
    high_low_diff = df["high"] - df["low"]
    open_close_diff = df["close"] - df["open"]
    high_close_diff = df["high"] - df["close"]
    high_open_diff = df["high"] - df["open"]
    
    # Define the conditions for the shooting star candle
    is_long_body = abs(open_close_diff) > 0.1 * high_low_diff
    is_upper_shadow_large = high_close_diff / (np.maximum(high_low_diff, 0.001)) > 0.6
    is_lower_shadow_small = high_open_diff / (np.maximum(high_low_diff, 0.001)) > 0.6
    is_large_range = high_low_diff > 3 * abs(open_close_diff)
    
    # Combine the conditions to identify shooting star candles
    shooting_star_condition = is_long_body & is_upper_shadow_large & is_lower_shadow_small & is_large_range
    
    # Add a new column for shooting star condition
    df["sstar"] = shooting_star_condition
    
    return df

def levels(ohlc_day):    
    """returns pivot point and support/resistance levels"""
    high = round(ohlc_day["high"][-1],2)
    low = round(ohlc_day["low"][-1],2)
    close = round(ohlc_day["close"][-1],2)
    pivot = round((high + low + close)/3,2)
    r1 = round((2*pivot - low),2)
    r2 = round((pivot + (high - low)),2)
    r3 = round((high + 2*(pivot - low)),2)
    s1 = round((2*pivot - high),2)
    s2 = round((pivot - (high - low)),2)
    s3 = round((low - 2*(high - pivot)),2)
    return (pivot,r1,r2,r3,s1,s2,s3)

def trend(ohlc_df,n):
    "function to assess the trend by analyzing each candle"
    df = ohlc_df.copy()
    df["up"] = np.where(df["low"]>=df["low"].shift(1),1,0)
    df["dn"] = np.where(df["high"]<=df["high"].shift(1),1,0)
    if df["close"][-1] > df["open"][-1]:
        if df["up"][-1*n:].sum() >= 0.7*n:
            return "uptrend"
    elif df["open"][-1] > df["close"][-1]:
        if df["dn"][-1*n:].sum() >= 0.7*n:
            return "downtrend"
    else:
        return None
   
def res_sup(ohlc_df,ohlc_day):
    """calculates closest resistance and support levels for a given candle"""
    level = ((ohlc_df["close"][-1] + ohlc_df["open"][-1])/2 + (ohlc_df["high"][-1] + ohlc_df["low"][-1])/2)/2
    p,r1,r2,r3,s1,s2,s3 = levels(ohlc_day)
    l_r1=level-r1
    l_r2=level-r2
    l_r3=level-r3
    l_p=level-p
    l_s1=level-s1
    l_s2=level-s2
    l_s3=level-s3
    lev_ser = pd.Series([l_p,l_r1,l_r2,l_r3,l_s1,l_s2,l_s3],index=["p","r1","r2","r3","s1","s2","s3"])
    sup = lev_ser[lev_ser>0].idxmin()
    res = lev_ser[lev_ser<0].idxmax()
    return (eval('{}'.format(res)), eval('{}'.format(sup)))

def candle_type(ohlc_df):    
    """returns the candle type of the last candle of an OHLC DF"""
    candle = None
    if doji(ohlc_df)["doji"].iloc[-1] == True:
        candle = "doji"    
    if maru_bozu(ohlc_df)["maru_bozu"].iloc[-1] == "maru_bozu_green":
        candle = "maru_bozu_green"   
    #if maru_bozu(ohlc_df)["maru_bozu"].iloc[-1] == "maru_bozu_red":

    if maru_bozu(ohlc_df)["maru_bozu"].iloc[-1] == "maru_bozu_red":
        candle = "maru_bozu_red"        
    if shooting_star(ohlc_df)["sstar"].iloc[-1] == True:
        candle = "shooting_star"        
    if hammer(ohlc_df)["hammer"].iloc[-1] == True:
        candle = "hammer"       
    return candle

def candle_pattern(ohlc_df, ohlc_day):    
    """returns the candle pattern identified"""
    
    # Define constants
    RANGE_THRESHOLD = 1.5
    TREND_PERIOD = 7
    
    # Initialize default values
    pattern = None
    signi = "low"
    
    # Get the average candle size
    avg_candle_size = abs(ohlc_df["close"] - ohlc_df["open"]).median()
    
    # Calculate support and resistance
    sup, res = res_sup(ohlc_df, ohlc_day)
    
    # Access the last two candle values for convenience
    close_last = ohlc_df["close"].iloc[-1]
    close_prev = ohlc_df["close"].iloc[-2]
    open_last = ohlc_df["open"].iloc[-1]
    open_prev = ohlc_df["open"].iloc[-2]
    high_last = ohlc_df["high"].iloc[-1]
    low_last = ohlc_df["low"].iloc[-1]
    high_prev = ohlc_df["high"].iloc[-2]
    low_prev = ohlc_df["low"].iloc[-2]
    
    # Check for significance based on support and resistance
    if (sup - RANGE_THRESHOLD * avg_candle_size) < close_last < (sup + RANGE_THRESHOLD * avg_candle_size):
        signi = "HIGH"
        
    if (res - RANGE_THRESHOLD * avg_candle_size) < close_last < (res + RANGE_THRESHOLD * avg_candle_size):
        signi = "HIGH"
    
    # Get candle type and trend
    candle = candle_type(ohlc_df)
    current_trend = trend(ohlc_df.iloc[:-1, :], TREND_PERIOD)
    
    # Define candle patterns
    if candle == 'doji':
        if close_last > close_prev and close_last > open_last:
            pattern = "doji_bullish"
        elif close_last < close_prev and close_last < open_last:
            pattern = "doji_bearish"
        elif current_trend == "uptrend" and high_last < close_prev and low_last > open_prev:
            pattern = "harami_cross_bearish"
        elif current_trend == "downtrend" and high_last < open_prev and low_last > close_prev:
            pattern = "harami_cross_bullish"
        
    if candle == "maru_bozu_green":
        pattern = "maru_bozu_bullish"
        
    if candle == "maru_bozu_red":
        pattern = "maru_bozu_bearish"
    
    if current_trend == "uptrend" and candle == "hammer":
        pattern = "hanging_man_bearish"
        
    if current_trend == "downtrend" and candle == "hammer":
        pattern = "hammer_bullish"
        
    if current_trend == "uptrend" and candle == "shooting_star":
        pattern = "shooting_star_bearish"
        
    if current_trend == "uptrend" and candle != "doji" and open_last > high_prev and close_last < low_prev:
        pattern = "engulfing_bearish"
        
    if current_trend == "downtrend" and candle != "doji" and close_last > high_prev and open_last < low_prev:
        pattern = "engulfing_bullish"
    
    return "Significance - {}, Pattern - {}".format(signi, pattern)


##############################################################################################

tickers = instrument_df


tickers = ["ZEEL","WIPRO","VEDL","ULTRACEMCO","UPL","TITAN","TECHM","TATASTEEL",
           "TATAMOTORS","TCS","SUNPHARMA","SBIN","SHREECEM","RELIANCE","POWERGRID",
           "ONGC","NESTLEIND","NTPC","MARUTI","M&M","LT","KOTAKBANK","JSWSTEEL","INFY",
           "INDUSINDBK","IOC","ITC","ICICIBANK","HDFC","HINDUNILVR","HINDALCO",
           "HEROMOTOCO","HDFCBANK","HCLTECH","GRASIM","GAIL","EICHERMOT","DRREDDY",
           "COALINDIA","CIPLA","BRITANNIA","INFRATEL","BHARTIARTL","BPCL","BAJAJFINSV",
           "BAJFINANCE","BAJAJ-AUTO","AXISBANK","ASIANPAINT","ADANIPORTS","IDEA",
           "MCDOWELL-N","UBL","NIACL","SIEMENS","SRTRANSFIN","SBILIFE","PNB",
           "PGHH","PFC","PEL","PIDILITIND","PETRONET","PAGEIND","OFSS","NMDC","NHPC",
           "MOTHERSUMI","MARICO","LUPIN","L&TFH","INDIGO","IBULHSGFIN","ICICIPRULI",
           "ICICIGI","HINDZINC","HINDPETRO","HAVELLS","HDFCLIFE","HDFCAMC","GODREJCP",
           "GICRE","DIVISLAB","DABUR","DLF","CONCOR","COLPAL","CADILAHC","BOSCHLTD",
           "BIOCON","BERGEPAINT","BANKBARODA","BANDHANBNK","BAJAJHLDNG","DMART",
           "AUROPHARMA","ASHOKLEY","AMBUJACEM","ADANITRANS","ACC",
           "WHIRLPOOL","WABCOINDIA","VOLTAS","VINATIORGA","VBL","VARROC","VGUARD",
           "UNIONBANK","UCOBANK","TRENT","TORNTPOWER","TORNTPHARM","THERMAX","RAMCOCEM",
           "TATAPOWER","TATACONSUM","TVSMOTOR","TTKPRESTIG","SYNGENE","SYMPHONY",
           "SUPREMEIND","SUNDRMFAST","SUNDARMFIN","SUNTV","STRTECH","SAIL","SOLARINDS",
           "SHRIRAMCIT","SCHAEFFLER","SANOFI","SRF","SKFINDIA","SJVN","RELAXO",
           "RAJESHEXPO","RECLTD","RBLBANK","QUESS","PRESTIGE","POLYCAB","PHOENIXLTD",
           "PFIZER","PNBHOUSING","PIIND","OIL","OBEROIRLTY","NAM-INDIA","NATIONALUM",
           "NLCINDIA","NBCC","NATCOPHARM","MUTHOOTFIN","MPHASIS","MOTILALOFS","MINDTREE",
           "MFSL","MRPL","MANAPPURAM","MAHINDCIE","M&MFIN","MGL","MRF","LTI","LICHSGFIN",
           "LTTS","KANSAINER","KRBL","JUBILANT","JUBLFOOD","JINDALSTEL","JSWENERGY",
           "IPCALAB","NAUKRI","IGL","IOB","INDHOTEL","INDIANB","IBVENTURES","IDFCFIRSTB",
           "IDBI","ISEC","HUDCO","HONAUT","HAL","HEXAWARE","HATSUN","HEG","GSPL",
           "GUJGASLTD","GRAPHITE","GODREJPROP","GODREJIND","GODREJAGRO","GLENMARK",
           "GLAXO","GILLETTE","GMRINFRA","FRETAIL","FCONSUMER","FORTIS","FEDERALBNK",
           "EXIDEIND","ESCORTS","ERIS","ENGINERSIN","ENDURANCE","EMAMILTD","EDELWEISS",
           "EIHOTEL","LALPATHLAB","DALBHARAT","CUMMINSIND","CROMPTON","COROMANDEL","CUB",
           "CHOLAFIN","CHOLAHLDNG","CENTRALBK","CASTROLIND","CANBK","CRISIL","CESC",
           "BBTC","BLUEDART","BHEL","BHARATFORG","BEL","BAYERCROP","BATAINDIA",
           "BANKINDIA","BALKRISIND","ATUL","ASTRAL","APOLLOTYRE","APOLLOHOSP",
           "AMARAJABAT","ALKEM","APLLTD","AJANTPHARM","ABFRL","ABCAPITAL","ADANIPOWER",
           "ADANIGREEN","ADANIGAS","ABBOTINDIA","AAVAS","AARTIIND","AUBANK","AIAENG","3MINDIA"]


def main():
   
  # Assuming tickers is a list of ticker symbols and you have defined fetchOHLC and candle_pattern functions
 result_list = []  # List to hold the results

 for ticker in tickers:
     try:
         # Fetch OHLC data
         ohlc = fetchOHLC(ticker, '5minute', 5)
         ohlc_day = fetchOHLC(ticker, 'day', 30)
         ohlc_day = ohlc_day.iloc[:-1, :]  

         # Get the candle pattern
         cp = candle_pattern(ohlc, ohlc_day)

         # Append the result to the list (ticker and cp value)
         result_list.append({'Ticker': ticker, 'CandlePattern': cp})
         print(ticker, ": ", cp)

     except Exception as e:
         # Handle any errors
         print(f"Skipping for {ticker}. Error: {e}")

 # Create a DataFrame from the collected results
 df = pd.DataFrame(result_list)

 # Display the resulting DataFrame
 print(df) 
        
# Continuous execution        
starttime=time.time()
timeout = time.time() + 60*60*1  # 60 seconds times 60 meaning the script will run for 1 hr
while time.time() <= timeout:
    try:
        print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main()
        time.sleep(300 - ((time.time() - starttime) % 300.0)) # 300 second interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
        
               
        
       
        
        