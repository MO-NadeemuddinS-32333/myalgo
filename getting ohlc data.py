# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 17:05:02 2025

@author: USER
"""

from kiteconnect import KiteConnect
import logging
import os
import datetime as dt
import pandas as pd

cwd = os.chdir("C:\\Users\\USER\\Desktop\\algo")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)
instrument_df.to_csv("NSE_Instruments_31122019.csv",index=False)


def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1

instrumentLookup(instrument_df, "IDEA")

def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


ohlc = fetchOHLC("ACC", "5minute", 5)