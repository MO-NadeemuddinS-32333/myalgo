import time
import logging
from datetime import datetime
import pandas as pd
from kiteconnect import KiteConnect

# === Strategy Configuration ===
ENTRY_PRICE = 80
STOP_LOSS = 130
TARGET_PRICE = 20
CHECK_INTERVAL = 30  # seconds
ENTRY_TIME = "09:20"  # strategy start time
SYMBOL = "BANKNIFTY"
lot_size = 15

# === Kite Connect setup ===
access_token = open("access_token.txt").read().strip()
api_key = open("api_key.txt").read().split()[0]
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

positions = {}
realized_pnl = 0

# === Logging setup ===
logging.basicConfig(
    filename="banknifty_strategy_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_option_chain():
    instruments = pd.DataFrame(kite.instruments("NFO"))
    instruments = instruments[instruments["name"] == SYMBOL]
    instruments = instruments[instruments["segment"] == "NFO-OPT"]
    expiry = instruments[instruments["instrument_type"] == "CE"]["expiry"].min()

    sample_option = instruments[instruments["instrument_type"] == "CE"].iloc[0]["tradingsymbol"]
    try:
        index_ltp = kite.ltp(f"NFO:{sample_option}")[f"NFO:{sample_option}"]["last_price"]
    except:
        raise Exception(f"Unable to fetch index price for sample option: {sample_option}")

    atm_strike = round(index_ltp / 100) * 100

    calls = instruments[(instruments["instrument_type"] == "CE") & (instruments["expiry"] == expiry)]
    puts = instruments[(instruments["instrument_type"] == "PE") & (instruments["expiry"] == expiry)]

    return calls, puts, atm_strike


def find_option_by_premium(options, target_price):
    min_diff = float('inf')
    best_symbol = None
    best_ltp = None

    for _, row in options.iterrows():
        symbol = row["tradingsymbol"]
        try:
            full_symbol = f"NFO:{symbol}"
            ltp = kite.ltp(full_symbol)[full_symbol]["last_price"]
            if abs(ltp - target_price) < min_diff:
                min_diff = abs(ltp - target_price)
                best_symbol = full_symbol
                best_ltp = ltp
        except:
            continue
    return best_symbol, best_ltp


def place_order(symbol):
    """Place a real order — currently commented for paper trade."""
    tradingsymbol = symbol.split(":")[1]
    logging.info(f"[LIVE ORDER] SELL {tradingsymbol}")

    # Uncomment for live trade:
    # kite.place_order(
    #     variety=kite.VARIETY_REGULAR,
    #     exchange="NFO",
    #     tradingsymbol=tradingsymbol,
    #     transaction_type=kite.TRANSACTION_TYPE_SELL,
    #     quantity=lot_size,
    #     order_type=kite.ORDER_TYPE_MARKET,
    #     product=kite.PRODUCT_MIS
    # )


def enter_trade():
    global positions
    calls, puts, _ = get_option_chain()
    ce_symbol, ce_ltp = find_option_by_premium(calls, ENTRY_PRICE)
    pe_symbol, pe_ltp = find_option_by_premium(puts, ENTRY_PRICE)

    if ce_symbol and pe_symbol:
        logging.info(f"[ENTRY] PAPER SELL CE: {ce_symbol} @ {ce_ltp}")
        logging.info(f"[ENTRY] PAPER SELL PE: {pe_symbol} @ {pe_ltp}")
        positions[ce_symbol] = {"entry_price": ce_ltp}
        positions[pe_symbol] = {"entry_price": pe_ltp}

        # For live trading: uncomment
        # place_order(ce_symbol)
        # place_order(pe_symbol)


def monitor_positions():
    global positions, realized_pnl
    to_close = []

    for symbol, data in positions.items():
        try:
            ltp = kite.ltp(symbol)[symbol]["last_price"]
            entry = data["entry_price"]
            if ltp >= STOP_LOSS:
                pnl = (entry - ltp) * lot_size
                logging.info(f"[SL HIT] {symbol} exited @ {ltp} | PnL: {pnl}")
                realized_pnl += pnl
                to_close.append(symbol)

                # For live trading: square off
                # kite.place_order(...BUY...)

            elif ltp <= TARGET_PRICE:
                pnl = (entry - ltp) * lot_size
                logging.info(f"[TARGET HIT] {symbol} exited @ {ltp} | PnL: {pnl}")
                realized_pnl += pnl
                to_close.append(symbol)

                # For live trading: square off
                # kite.place_order(...BUY...)
        except:
            continue

    for s in to_close:
        del positions[s]

    if not positions:
        logging.info(f"[RE-ENTRY] No open positions. Re-entering. PnL so far: {realized_pnl}")
        enter_trade()


def run_strategy():
    logging.info("Waiting for strategy start time...")
    while datetime.now().strftime("%H:%M") < ENTRY_TIME:
        time.sleep(10)

    logging.info("Starting strategy now...")
    enter_trade()

    while True:
        monitor_positions()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_strategy()
