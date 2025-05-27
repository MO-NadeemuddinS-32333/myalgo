import pandas as pd
from datetime import datetime

# Assume fetchOHLC, simulate_trade, and kite are defined elsewhere

papertrading = 1  # 1 for paper trading, 0 for live trading
capital_per_trade = 10000

# === Strategy Utilities ===
def rsi(df, n=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
    RS = gain / loss
    return 100 - (100 / (1 + RS))

# === Common Order Execution ===
def place_order(symbol, side, quantity, price):
    if papertrading:
        position = "LONG" if side == "buy" else "SHORT"
        simulate_trade(symbol, position, price)
    else:
        t_type = kite.TRANSACTION_TYPE_BUY if side == "buy" else kite.TRANSACTION_TYPE_SELL
        kite.place_order(
            tradingsymbol=symbol,
            exchange=kite.EXCHANGE_NSE,
            transaction_type=t_type,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS,
            variety=kite.VARIETY_REGULAR
        )

# === Trend-Following Strategy (Supertrend already implemented elsewhere) ===
def supertrend_strategy(symbol, df):
    pass  # Assume handled in your existing code

# === Mean Reversion Strategy ===
def mean_reversion_strategy(symbol, df):
    df['RSI'] = rsi(df)
    ltp = df['close'].iloc[-1]
    qty = int(capital_per_trade / ltp)

    if df['RSI'].iloc[-1] < 30:
        place_order(symbol, 'buy', qty, ltp)
    elif df['RSI'].iloc[-1] > 70:
        place_order(symbol, 'sell', qty, ltp)

# === Breakout Strategy (ORB) ===
def orb_strategy(symbol, df):
    df.index = pd.to_datetime(df.index)
    open_range = df.between_time("09:15", "09:30")
    orb_high = open_range['high'].max()
    orb_low = open_range['low'].min()
    ltp = df['close'].iloc[-1]
    qty = int(capital_per_trade / ltp)

    if ltp > orb_high:
        place_order(symbol, 'buy', qty, ltp)
    elif ltp < orb_low:
        place_order(symbol, 'sell', qty, ltp)

# === Strategy Selector ===
def run_strategy(strategy_name, symbol):
    df = fetchOHLC(symbol, interval='5minute', days=5)

    if strategy_name == 'mean_reversion':
        mean_reversion_strategy(symbol, df)
    elif strategy_name == 'breakout':
        orb_strategy(symbol, df)
    elif strategy_name == 'trend_following':
        supertrend_strategy(symbol, df)
    else:
        print(f"Invalid strategy: {strategy_name}")

# === Example Usage ===
symbols = ['RELIANCE', 'TCS', 'APOLLOPIPE']
strategy_to_run = 'mean_reversion'  # Can be 'mean_reversion', 'breakout', or 'trend_following'

for symbol in symbols:
    run_strategy(strategy_to_run, symbol)
