# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 18:36:47 2025

@author: USER
"""

#for all functions visit: https://github.com/zerodha/pykiteconnect/blob/master/kiteconnect/connect.py#L321

from kiteconnect import KiteConnect
import os


# Fetch quote details
quote = kite.quote("NSE:INFY")

# Fetch last trading price of an instrument
ltp = kite.ltp("NSE:INFY")



# Fetch order details
orders = kite.orders()

# Fetch position details
positions = kite.positions()




# Fetch holding details
holdings = kite.holdings()

profile = kite.profile()

margins = kite.margins()

holdings = kite.holdings()