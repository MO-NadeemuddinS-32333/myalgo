# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 05:46:49 2025

@author: USER
"""

from kiteconnect import KiteConnect
import logging
import os
from kiteconnect import KiteConnect
import pandas as pd


api_key = "jyheto7j2tbcjutp"
api_secret = "o4wxe6qt7cnay0kd0ymybecevg0pnvgi"
kite = KiteConnect(api_key=api_key)
print(kite.login_url()) #use this url to manually login and authorize yourself

#generate trading session
request_token = "8oZcKJz2LpU75adbeZ4e8J7bZYaAmbNV" #Extract request token from the redirect url obtained after you authorize yourself by loggin in
data = kite.generate_session(request_token, api_secret=api_secret)


#create kite trading object
kite.set_access_token(data["access_token"])


def placeMarketOrder(symbol,buy_sell,quantity):    
    # Place an intraday market order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
    def placeOrder(symbol,buy_sell,quantity, price):    
        # Place an intraday market order on NSE
        if buy_sell == "buy":
            t_type=kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "sell":
            t_type=kite.TRANSACTION_TYPE_SELL
        kite.place_order(tradingsymbol=symbol,
                        exchange=kite.EXCHANGE_NSE,
                        transaction_type=t_type,
                        quantity=quantity,
                        order_type=kite.ORDER_TYPE_LIMIT,
                        price=price,
                        product=kite.PRODUCT_MIS,
                        variety=kite.VARIETY_REGULAR)
    
    def placeamoOrder(symbol,buy_sell,quantity, price):    
        # Place an intraday market order on NSE
        if buy_sell == "buy":
            t_type=kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "sell":
            t_type=kite.TRANSACTION_TYPE_SELL
        kite.place_order(tradingsymbol=symbol,
                        exchange=kite.EXCHANGE_NSE,
                        transaction_type=t_type,
                        quantity=quantity,
                        order_type=kite.VARIETY_AMO,
                        price=price,
                        product=kite.PRODUCT_MIS,
                        variety=kite.VARIETY_REGULAR)
        
        
        
        def placeStopOrder(symbol,buy_sell,quantity, price,triggerprice):    
            # Place an intraday market order on NSE
            if buy_sell == "buy":
                t_type=kite.TRANSACTION_TYPE_BUY
            elif buy_sell == "sell":
                t_type=kite.TRANSACTION_TYPE_SELL
            kite.place_order(tradingsymbol=symbol,
                            exchange=kite.EXCHANGE_NSE,
                            transaction_type=t_type,
                            quantity=quantity,
                            order_type=kite.ORDER_TYPE_SL,
                            price=price,
                            trigger_price=triggerprice,
                            product=kite.PRODUCT_MIS,
                            variety=kite.VARIETY_REGULAR)
            
            
            placeMarketOrder("IDEA","sell", 300)
            placeOrder("IDEA","sell",300,7.49) 
    
            placeStopOrder("IDEA", "buy", 300, 8.02, 8)

            placeOrder("NIFTYBEES", "buy", 300, 248)
            
          
            
            

    
    
    for i in range(10):
    # Call the placeOrder method with decreasing price
        placeOrder("IDEA", "buy", 1, 7.5 - i * 0.01)
    

    
def placeBracketOrder(symbol,buy_sell,quantity,atr,price):    
    # Place an intraday market order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    price=price, #BO has to be a limit order, set a low price threshold
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_BO,
                    squareoff=int(6*atr), 
                    stoploss=int(3*atr), 
                    trailing_stoploss=2)
    
    placeBracketOrder("YESBANK", "buy", 10 , 2, 17.11)
  