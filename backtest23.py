#!pip install ta

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from kiteconnect import KiteConnect
import datetime
import os
import warnings



cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")


#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


def fetch_data(symbol, interval="5minute", days=100):
    instruments = kite.instruments()
    instrument_df = pd.DataFrame(instruments)
    
    # Check if symbol exists
    row = instrument_df[instrument_df['tradingsymbol'] == symbol]
    if row.empty:
        raise ValueError(f"{symbol} not found in instruments.")
    
    instrument_token = row['instrument_token'].values[0]

    to_date = datetime.datetime.now()
    from_date = to_date - datetime.timedelta(days=days)
    
    data = kite.historical_data(instrument_token, from_date, to_date, interval)
    df = pd.DataFrame(data)
    
    df.set_index("date", inplace=True)
    df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
    return df


def atr(DF, n):
    df = DF.copy()
    df['H-L'] = abs(df['High'] - df['Low'])
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
    df['ATR'] = df['TR'].ewm(com=n, min_periods=n).mean()
    return df['ATR']


def supertrend(DF, n, m, label):
    df = DF.copy()
    df['ATR'] = atr(df, n)
    df["Upper Band"] = ((df['High'] + df['Low']) / 2) + m * df['ATR']
    df["Lower Band"] = ((df['High'] + df['Low']) / 2) - m * df['ATR']
    df["in_uptrend"] = True

    for current in range(1, len(df)):
        prev = current - 1

        if df['Close'].iloc[current] > df['Upper Band'].iloc[prev]:
            df.loc[df.index[current], "in_uptrend"] = True
        elif df['Close'].iloc[current] < df['Lower Band'].iloc[prev]:
            df.loc[df.index[current], "in_uptrend"] = False
        else:
            df.loc[df.index[current], "in_uptrend"] = df["in_uptrend"].iloc[prev]
            if df["in_uptrend"].iloc[current] and df["Lower Band"].iloc[current] < df["Lower Band"].iloc[prev]:
                df.loc[df.index[current], "Lower Band"] = df["Lower Band"].iloc[prev]
            if not df["in_uptrend"].iloc[current] and df["Upper Band"].iloc[current] > df["Upper Band"].iloc[prev]:
                df.loc[df.index[current], "Upper Band"] = df["Upper Band"].iloc[prev]

    df[f'Strend_{label}'] = np.where(df['in_uptrend'], df['Lower Band'], df['Upper Band'])
    df[f'ST_DIR_{label}'] = np.where(df['in_uptrend'], 1, -1)
    return df






def generate_signals(df):
    df['Buy'] = ((df['ST_DIR_7_3'] == 1) & 
                 (df['ST_DIR_10_3'] == 1) & 
                 (df['ST_DIR_11_2'] == 1))
    
    df['Sell'] = ((df['ST_DIR_7_3'] == -1) & 
                  (df['ST_DIR_10_3'] == -1) & 
                  (df['ST_DIR_11_2'] == -1))
    return df

def backtest(df, initial_capital=100000, sl_pct=0.01, target_pct=0.02):
    position = 0
    capital = initial_capital
    entry_price = 0
    trades = []

    for i in range(1, len(df)):
        if position == 0 and df['Buy'].iloc[i-1]:
            position = capital // df['Close'].iloc[i]
            entry_price = df['Close'].iloc[i]
            capital -= position * entry_price
            trades.append({'type': 'Buy', 'price': entry_price, 'time': df.index[i]})

        elif position > 0:
            high = df['High'].iloc[i]
            low = df['Low'].iloc[i]

            if low <= entry_price * (1 - sl_pct):
                exit_price = entry_price * (1 - sl_pct)
                capital += position * exit_price
                trades.append({'type': 'SL', 'price': exit_price, 'time': df.index[i]})
                position = 0

            elif high >= entry_price * (1 + target_pct):
                exit_price = entry_price * (1 + target_pct)
                capital += position * exit_price
                trades.append({'type': 'Target', 'price': exit_price, 'time': df.index[i]})
                position = 0

            elif df['Sell'].iloc[i]:
                exit_price = df['Close'].iloc[i]
                capital += position * exit_price
                trades.append({'type': 'Exit', 'price': exit_price, 'time': df.index[i]})
                position = 0

    final_value = capital + (position * df['Close'].iloc[-1] if position else 0)
    return trades, final_value

def calculate_kpis(trades, initial_capital, final_value):
    total_trades = len([t for t in trades if t['type'] == 'Buy'])
    wins = sum(1 for i in range(1, len(trades)) if trades[i]['type'] in ['Target'] and trades[i-1]['type'] == 'Buy')
    losses = sum(1 for i in range(1, len(trades)) if trades[i]['type'] in ['SL'] and trades[i-1]['type'] == 'Buy')
    pnl = final_value - initial_capital

    return {
        "Total Trades": total_trades,
        "Winning Trades": wins,
        "Losing Trades": losses,
        "Win Rate (%)": round((wins / total_trades) * 100 if total_trades else 0, 2),
        "Net PnL": round(pnl, 2),
        "Return (%)": round((pnl / initial_capital) * 100, 2)
    }

# --- Run Backtest ---
symbols =  ["360ONE", "3MINDIA", "ABB", "ACC", "ACMESOLAR", "AIAENG", "APLAPOLLO", "AUBANK", "AWL", "AADHARHFC",
"AARTIIND", "AAVAS", "ABBOTINDIA", "ACE", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL",
"ABCAPITAL", "ABFRL", "ABREL", "ABSLAMC", "AEGISLOG", "AFCONS", "AFFLE", "AJANTPHARM", "AKUMS", "APLLTD",
"ALIVUS", "ALKEM", "ALKYLAMINE", "ALOKINDS", "ARE&M", "AMBER", "AMBUJACEM", "ANANDRATHI", "ANANTRAJ", "ANGELONE",
"APARINDS", "APOLLOHOSP", "APOLLOTYRE", "APTUS", "ASAHIINDIA", "ASHOKLEY", "ASIANPAINT", "ASTERDM", "ASTRAZEN", "ASTRAL",
"ATUL", "AUROPHARMA", "AIIL", "DMART", "AXISBANK", "BASF", "BEML", "BLS", "BSE", "BAJAJ-AUTO",
"BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BAJAJHFL", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "MAHABANK",
"BATAINDIA", "BAYERCROP", "BERGEPAINT", "BDL", "BEL", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BHARTIHEXA",
"BIKAJI", "BIOCON", "BSOFT", "BLUEDART", "BLUESTARCO", "BBTC", "BOSCHLTD", "FIRSTCRY", "BRIGADE", "BRITANNIA",
"MAPMYINDIA", "CCL", "CESC", "CGPOWER", "CRISIL", "CAMPUS", "CANFINHOME", "CANBK", "CAPLIPOINT", "CGCL",
"CARBORUNIV", "CASTROLIND", "CEATLTD", "CENTRALBK", "CDSL", "CENTURYPLY", "CERA", "CHALET", "CHAMBLFERT", "CHENNPETRO",
"CHOLAHLDNG", "CHOLAFIN", "CIPLA", "CUB", "CLEAN", "COALINDIA", "COCHINSHIP", "COFORGE", "COLPAL", "CAMS",
"CONCORDBIO", "CONCOR", "COROMANDEL", "CRAFTSMAN", "CREDITACC", "CROMPTON", "CUMMINSIND", "CYIENT", "DCMSHRIRAM", "DLF",
"DOMS", "DABUR", "DALBHARAT", "DATAPATTNS", "DEEPAKFERT", "DEEPAKNTR", "DELHIVERY", "DEVYANI", "DIVISLAB", "DIXON",
"LALPATHLAB", "DRREDDY", "EIDPARRY", "EIHOTEL", "EICHERMOT", "ELECON", "ELGIEQUIP", "EMAMILTD",
"EMCURE", "ENDURANCE", "ENGINERSIN", "ERIS", "ESCORTS", "ETERNAL", "EXIDEIND", "NYKAA", "FEDERALBNK", "FACT",
"FINCABLES", "FINPIPE", "FSL", "FIVESTAR", "FORTIS", "GAIL", "GVT&D", "GMRAIRPORT", "GRSE", "GICRE",
"GILLETTE", "GLAND", "GLAXO", "GLENMARK", "MEDANTA", "GODIGIT", "GPIL", "GODFRYPHLP", "GODREJAGRO", "GODREJCP",
"GODREJIND", "GODREJPROP", "GRANULES", "GRAPHITE", "GRASIM", "GRAVITA", "GESHIP", "FLUOROCHEM", "GUJGASLTD", "GMDCLTD",
"GNFC", "GPPL", "GSPL", "HEG", "HBLENGINE", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL",
"HAPPSTMNDS", "HAVELLS", "HEROMOTOCO", "HSCL", "HINDALCO", "HAL", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "HINDZINC",
"POWERINDIA", "HOMEFIRST", "HONASA", "HONAUT", "HUDCO", "HYUNDAI", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDBI",
"IDFCFIRSTB", "IFCI", "IIFL", "INOXINDIA", "IRB", "IRCON", "ITC", "ITI", "INDGN", "INDIACEM",
"INDIAMART", "INDIANB", "IEX", "INDHOTEL", "IOC", "IOB", "IRCTC", "IRFC", "IREDA", "IGL",
"INDUSTOWER", "INDUSINDBK", "NAUKRI", "INFY", "INOXWIND", "INTELLECT", "INDIGO", "IGIL", "IKS", "IPCALAB",
"JBCHEPHARM", "JKCEMENT", "JBMA", "JKTYRE", "JMFINANCIL", "JSWENERGY", "JSWHL", "JSWINFRA", "JSWSTEEL", "JPPOWER",
"J&KBANK", "JINDALSAW", "JSL", "JINDALSTEL", "JIOFIN", "JUBLFOOD", "JUBLINGREA", "JUBLPHARMA", "JWL", "JUSTDIAL",
"JYOTHYLAB", "JYOTICNC", "KPRMILL", "KEI", "KNRCON", "KPITTECH", "KAJARIACER", "KPIL", "KALYANKJIL", "KANSAINER",
"KARURVYSYA", "KAYNES", "KEC", "KFINTECH", "KIRLOSBROS", "KIRLOSENG", "KOTAKBANK", "KIMS", "LTF", "LTTS",
"LICHSGFIN", "LTFOODS", "LTIM", "LT", "LATENTVIEW", "LAURUSLABS", "LEMONTREE", "LICI", "LINDEINDIA", "LLOYDSME",
"LUPIN", "MMTC", "MRF", "LODHA", "MGL", "MAHSEAMLES", "M&MFIN", "M&M", "MANAPPURAM", "MRPL",
"MANKIND", "MARICO", "MARUTI", "MASTEK", "MFSL", "MAXHEALTH", "MAZDOCK", "METROPOLIS", "MINDACORP", "MSUMI",
"MOTILALOFS", "MPHASIS", "MCX", "MUTHOOTFIN", "NATCOPHARM", "NBCC", "NCC", "NHPC", "NLCINDIA", "NMDC",
"NSLNISP", "NTPCGREEN", "NTPC", "NH", "NATIONALUM", "NAVA", "NAVINFLUOR", "NESTLEIND", "NETWEB", "NETWORK18",
"NEULANDLAB", "NEWGEN", "NAM-INDIA", "NIVABUPA", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "OLAELEC", "OLECTRA",
"PAYTM", "OFSS", "POLICYBZR", "PCBL", "PGEL", "PIIND", "PNBHOUSING", "PNCINFRA", "PTCIL", "PVRINOX",
"PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", "PFIZER", "PHOENIXLTD", "PIDILITIND", "PEL", "PPLPHARMA", "POLYMED",
"POLYCAB", "POONAWALLA", "PFC", "POWERGRID", "PRAJIND", "PREMIERENE", "PRESTIGE", "PNB", "RRKABEL", "RBLBANK",
"RECLTD", "RHIM", "RITES", "RADICO", "RVNL", "RAILTEL", "RAINBOW", "RKFORGE", "RCF", "RTNINDIA",
"RAYMONDLSL", "RAYMOND", "REDINGTON", "RELIANCE", "RPOWER", "ROUTE", "SBFC", "SBICARD", "SBILIFE", "SJVN",
"SKFINDIA", "SRF", "SAGILITY", "SAILIFE", "SAMMAANCAP", "MOTHERSON", "SAPPHIRE", "SARDAEN", "SAREGAMA", "SCHAEFFLER",
"SCHNEIDER", "SCI", "SHREECEM", "RENUKA", "SHRIRAMFIN", "SHYAMMETL", "SIEMENS", "SIGNATURE", "SOBHA", "SOLARINDS",
"SONACOMS", "SONATSOFTW", "STARHEALTH", "SBIN", "SAIL", "SWSOLAR", "SUMICHEM", "SUNPHARMA", "SUNTV", "SUNDARMFIN",
"SUNDRMFAST", "SUPREMEIND", "SUVENPHAR", "SUZLON", "SWANENERGY", "SWIGGY", "SYNGENE", "SYRMA", "TBOTEK", "TVSMOTOR",
"TANLA", "TATACHEM", "TATACOMM", "TCS", "TATACONSUM", "TATAELXSI", "TATAINVEST", "TATAMOTORS", "TATAPOWER", "TATASTEEL",
"TATATECH", "TTML", "TECHM", "TECHNOE", "TEJASNET", "NIACL", "RAMCOCEM", "THERMAX", "TIMKEN", "TITAGARH",
"TITAN", "TORNTPHARM", "TORNTPOWER", "TARIL", "TRENT", "TRIDENT", "TRIVENI", "TRITURBINE", "TIINDIA", "UCOBANK",
"UNOMINDA", "UPL", "UTIAMC", "ULTRACEMCO", "UNIONBANK", "UBL", "UNITDSPR", "USHAMART", "VGUARD", "DBREALTY",
"VTL", "VBL", "MANYAVAR", "VEDL", "VIJAYA", "VMM", "IDEA", "VOLTAS", "WAAREEENER", "WELCORP",
"WELSPUNLIV", "WESTLIFE", "WHIRLPOOL", "WIPRO", "WOCKPHARMA", "YESBANK", "ZFCVINDIA", "ZEEL", "ZENTEC", "ZENSARTECH",
"ZYDUSLIFE", "ECLERX"]

results = []

for sym in symbols:
    print(f"\n🔍 Backtesting {sym}")
    try:
        df = fetch_data(sym).copy()
        df = supertrend(df, 7, 3, "7_3")
        df = supertrend(df, 10, 3, "10_3")
        df = supertrend(df, 11, 2, "11_2")
        df = generate_signals(df)

        trades, final_value = backtest(df)
        kpis = calculate_kpis(trades, 100000, final_value)
        kpis["Symbol"] = sym
        results.append(kpis)
    except Exception as e:
        print(f"⚠️ Error with {sym}: {e}")

        

# Suppress FutureWarnings globally
warnings.simplefilter(action='ignore', category=FutureWarning)

        
        
summary_df = pd.DataFrame(results)
summary_df = summary_df.sort_values("Return (%)", ascending=False)
print(summary_df)
summary_df.to_csv("backtest_summary.csv", index=False)

       
# Convert relevant columns to numeric in case they're strings
summary_df['Win Rate (%)'] = pd.to_numeric(summary_df['Win Rate (%)'], errors='coerce')
summary_df['Return (%)'] = pd.to_numeric(summary_df['Return (%)'], errors='coerce')
summary_df['Net PnL'] = pd.to_numeric(summary_df['Net PnL'], errors='coerce')

filtered_df = summary_df[
    (summary_df['Win Rate (%)'] > 30) &
    (summary_df['Return (%)'] > 30) &
    (summary_df['Net PnL'] > 10000)
]

print(filtered_df)


symbol_list = filtered_df['Symbol'].tolist()
print(symbol_list)



# --- Output Results ---
for k, v in kpis.items():
    print(f"{k}: {v}")

# --- Plotting signals (optional) ---
plt.figure(figsize=(14,6))
plt.plot(df['Close'], label='Close Price')
for trade in trades:
    color = 'g' if trade['type'] == 'Buy' else 'r'
    plt.scatter(trade['time'], trade['price'], color=color, marker='^' if trade['type'] == 'Buy' else 'v')
plt.title(f"Trades for {sym}")
plt.legend()
plt.show()
