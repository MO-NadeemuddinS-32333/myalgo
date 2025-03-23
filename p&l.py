# -*- coding: utf-8 -*-
"""
Created on Sun Mar 23 04:42:11 2025

@author: USER
"""
from kiteconnect import KiteConnect
import datetime




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

# Call the function to get P&L
get_pnl()