#pip install yfinance
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import os
import numpy as np

cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")

nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Step 1: Fetch all NSE stock symbols (top ~200 for demo)
def get_nse_symbols(limit=700):
    sample_symbols =   ["360ONE", "3MINDIA", "ABB", "ACC", "ACMESOLAR", "AIAENG", "APLAPOLLO", "AUBANK", "AWL", "AADHARHFC",
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
    
    return [sym + ".NS" for sym in sample_symbols[:limit]]



# Step 2: Download price and volume data
def fetch_market_data(symbols, start_date, end_date):
    data = yf.download(symbols, start=start_date, end=end_date, group_by='ticker', threads=True)
    return data

# Step 3: Get news sentiment for a stock from Moneycontrol
def get_news_sentiment(symbol):
    url = f"https://www.moneycontrol.com/news/tags/{symbol.lower()}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    headlines = [tag.get_text() for tag in soup.select(".clearfix h2")[:5]]
    scores = [sid.polarity_scores(text)['compound'] for text in headlines]
    return round(sum(scores) / len(scores), 2) if scores else 0

# Execution starts
symbols = get_nse_symbols(limit=700)  # You can increase to 200+
end_date = datetime.today().date() - timedelta(days=1)
start_date = end_date - timedelta(days=7)

data = fetch_market_data(symbols, start_date, end_date)

results = []

for symbol in symbols:
    try:
        close = data[symbol]['Close']
        volume = data[symbol]['Volume']
        price_change = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100
        avg_vol = volume[:-1].mean()
        vol_surge = ((volume.iloc[-1] - avg_vol) / avg_vol) * 100
        sentiment = get_news_sentiment(symbol.replace('.NS', ''))

        results.append({
            'Symbol': symbol,
            'Price Change %': round(price_change, 2),
            'Volume Surge %': round(vol_surge, 2),
            'News Sentiment': sentiment
        })
    except Exception as e:
        print(e)
        continue  # Skip problematic symbols

# Final sorted DataFrame
df_result = pd.DataFrame(results)
df_result = df_result.sort_values(by='Price Change %', ascending=False)
# Save to Excel
df_result.to_excel("sorted_results.xlsx", index=False)

# Sort by low volume and high sentiment
filtered_df = df_result.sort_values(by=['Volume Surge %', 'News Sentiment'], ascending=[True, False])

filtered_df.to_excel("filtered result.xlsx", index=False)

#use this important dataset
toppicksdataset_df =df_result[
    (np.abs(df_result['Volume Surge %']) < 20) & 
    (np.abs(df_result['News Sentiment']) > 0.2)
]

toppicksdataset_df.to_excel("low volume.xlsx", index=False)

print("Top Potential Movers with Sentiment:")
print(df_result.head(20))


bullish = df_result[df_result['News Sentiment'] > 0]
print("++++++++++++++++++++++++++++++++++++++" + "Bullish" + "+++++++++++++++++++++++++++++++++")
print(bullish.head(10))
print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")


bearish = df_result[df_result['News Sentiment'] < 0]
print("++++++++++++++++++++++++++++++++++++++" + "Bearish" + "+++++++++++++++++++++++++++++++++")
print(bearish.head(10))
print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")




df_result.head(10).plot(x='Symbol', y=['Price Change %', 'Volume Surge %', 'News Sentiment'], kind='bar')
plt.title('Top 10 Movers: Price, Volume & Sentiment')
plt.show()

