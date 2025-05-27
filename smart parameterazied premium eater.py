import time
import logging
from datetime import datetime
import pandas as pd
from kiteconnect import KiteConnect
import os

# === Strategy Configuration ===
ENTRY_PRICE = 250
STOP_LOSS = 350
TARGET_PRICE = 140
CHECK_INTERVAL = 2  # seconds
ENTRY_TIME = "09:35"
SYMBOL = "BANKNIFTY"
lot_size = 30
PAPER_TRADE = True  # Set to False to go live

cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")
    

# === Kite Setup ===
access_token = open("access_token.txt").read().strip()
api_key = open("api_key.txt").read().split()[0]
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)


#cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")
    

# === Logging Setup ===
logging.basicConfig(
    filename="19_MAYY25_banknifty_strategy_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

positions = {}
realized_pnl = 0


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


def place_order(symbol, transaction_type):
    tradingsymbol = symbol.split(":")[1]
    if PAPER_TRADE:
        logging.info(f"[PAPER ORDER] {transaction_type} {tradingsymbol}")
        return "paper_order_id"
    else:
        logging.info(f"[LIVE ORDER] {transaction_type} {tradingsymbol}")
        return kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange="NFO",
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=lot_size,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS
        )
    print("order placed.... successfully")


def place_sl_order(symbol, trigger_price):
    tradingsymbol = symbol.split(":")[1]
    if PAPER_TRADE:
        logging.info(f"[PAPER SL ORDER] BUY {tradingsymbol} @ {trigger_price}")
        return "paper_sl_order_id"
    else:
        logging.info(f"[LIVE SL ORDER] BUY {tradingsymbol} @ {trigger_price}")
        return kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange="NFO",
            tradingsymbol=tradingsymbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=lot_size,
            order_type=kite.ORDER_TYPE_SLM,
            product=kite.PRODUCT_MIS,
            trigger_price=trigger_price
        )


def cancel_order(order_id):
    if PAPER_TRADE:
        logging.info(f"[PAPER CANCEL] Order {order_id} cancelled.")
    else:
        try:
            kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=order_id)
            logging.info(f"[CANCEL] Order {order_id} cancelled.")
        except Exception as e:
            logging.error(f"[CANCEL ERROR] {e}")


def enter_trade():
    global positions
    calls, puts, _ = get_option_chain()
    ce_symbol, ce_ltp = find_option_by_premium(calls, ENTRY_PRICE)
    pe_symbol, pe_ltp = find_option_by_premium(puts, ENTRY_PRICE)

    if ce_symbol and pe_symbol:
        logging.info(f"[ENTRY] SELL CE: {ce_symbol} @ {ce_ltp}")
        logging.info(f"[ENTRY] SELL PE: {pe_symbol} @ {pe_ltp}")
        positions[ce_symbol] = {"entry_price": ce_ltp, "sl_order_id": None}
        positions[pe_symbol] = {"entry_price": pe_ltp, "sl_order_id": None}

        ce_sl_id = place_sl_order(ce_symbol, STOP_LOSS)
        pe_sl_id = place_sl_order(pe_symbol, STOP_LOSS)

        positions[ce_symbol]["sl_order_id"] = ce_sl_id
        positions[pe_symbol]["sl_order_id"] = pe_sl_id

        place_order(ce_symbol, kite.TRANSACTION_TYPE_SELL)
        place_order(pe_symbol, kite.TRANSACTION_TYPE_SELL)


def monitor_positions():
    global positions, realized_pnl
    to_close = []

    for symbol, data in positions.items():
        try:
            ltp = kite.ltp(symbol)[symbol]["last_price"]
            entry = data["entry_price"]
            if ltp >= STOP_LOSS or ltp <= TARGET_PRICE:
                pnl = (entry - ltp) * lot_size
                reason = "SL HIT" if ltp >= STOP_LOSS else "TARGET HIT"
                logging.info(f"[{reason}] {symbol} exited @ {ltp} | PnL: {pnl}")
                realized_pnl += pnl
                to_close.append(symbol)

                sl_order_id = data.get("sl_order_id")
                if sl_order_id:
                    cancel_order(sl_order_id)

                place_order(symbol, kite.TRANSACTION_TYPE_BUY)
        except Exception as e:
            logging.error(f"[ERROR] Monitoring {symbol}: {e}")

    for s in to_close:
        del positions[s]

    if not positions:
        logging.info(f"[RE-ENTRY] No open positions at {datetime.now().strftime('%H:%M:%S')}. Re-entering...")
        enter_trade()


def wait_until_entry_time():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now >= ENTRY_TIME:
            logging.info(f"[START] Entry time reached at {now}")
            break
        logging.info(f"[WAITING] Current time {now}, waiting for {ENTRY_TIME}")
        time.sleep(15)


def main():
    logging.info("==== Starting BankNIFTY Strategy (Paper Trade Mode) ====")
    wait_until_entry_time()
    enter_trade()

    while True:
        monitor_positions()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
