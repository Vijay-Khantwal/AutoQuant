import yfinance as yf
from niftystocks import ns
import pandas as pd
import numpy as np
import lightgbm as lgb
import logging
import warnings
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & SCHEMA ---
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

MIN_PRICE = 50.0
MIN_VOLUME = 100000
MAX_STALE_DAYS = 6   # Increased to 6 to survive long weekend holidays

FEATURE_COLS = [
    'Intraday_Range', 'Close_Open_Momentum', 'Top_Wick_Rejection',
    'Dist_SMA_10', 'Dist_SMA_50', 'Volume_Ratio',
    'Relative_Strength_10d', 'Market_Regime_200'
]

# --- 2. LOAD TRAINED MODEL ---
if not os.path.exists('nifty500_model.txt'):
    print("Error: 'nifty500_model.txt' not found. Run train.py first.")
    exit()

bst = lgb.Booster(model_file='nifty500_model.txt')

# --- 3. FETCH RECENT LIVE SNAPSHOT ---
print("Fetching live market snapshot...")
end_date = datetime.today()
# FIX: Increased from 320 to 400 calendar days to guarantee 250+ trading days
start_date = end_date - timedelta(days=400)

raw_basket = ns.get_nifty500_with_ns()
known_delisted = ['HDFC.NS', 'TATAMOTORS.NS', 'MOTHERSUMI.NS', 'MINDAIND.NS', 'IBULHSGFIN.NS', 'FRETAIL.NS']
stock_basket = [t for t in raw_basket if t not in known_delisted]

raw_data = yf.download(
    stock_basket, 
    start=start_date.strftime('%Y-%m-%d'), 
    end=end_date.strftime('%Y-%m-%d'), 
    progress=False, 
    threads=True, 
    group_by='ticker'
)

nifty_df = yf.Ticker('^NSEI').history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
nifty_df['Nifty_SMA_200'] = nifty_df['Close'].rolling(window=200).mean()
nifty_df['Market_Regime_200'] = nifty_df['Close'] / nifty_df['Nifty_SMA_200'] - 1
nifty_df['Nifty_Return_10d'] = nifty_df['Close'] / nifty_df['Close'].shift(10) - 1
macro_features = nifty_df[['Market_Regime_200', 'Nifty_Return_10d']].copy().tz_localize(None)

# --- 4. FEATURE EXTRACTION & SAFEGUARD GUARDS ---
live_rows, valid_tickers, last_prices = [], [], []
available_tickers = list(set([col[0] for col in raw_data.columns]))
cutoff_date = datetime.today() - timedelta(days=MAX_STALE_DAYS)

for ticker in available_tickers:
    try:
        df = raw_data[ticker].copy()
        if df['Close'].isna().all() or len(df.dropna()) < 220:
            continue
            
        df.index = df.index.tz_localize(None)
        
        # GUARD 1: Stale Data Filter
        latest_date = df.index[-1]
        if latest_date < cutoff_date:
            continue
            
        latest_close = df['Close'].iloc[-1]
        latest_avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        
        # GUARD 2: Live Price and Liquidity Filter
        if latest_close < MIN_PRICE or latest_avg_vol < MIN_VOLUME:
            continue
            
        df = df.join(macro_features, how='inner')
        
        df['Intraday_Range'] = (df['High'] - df['Low']) / df['Open']
        df['Close_Open_Momentum'] = (df['Close'] - df['Open']) / df['Open']
        df['Top_Wick_Rejection'] = (df['High'] - df[['Open', 'Close']].max(axis=1)) / df['Open']
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Dist_SMA_10'] = df['Close'] / df['SMA_10'] - 1
        df['Dist_SMA_50'] = df['Close'] / df['SMA_50'] - 1
        
        rolling_vol = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = np.where(rolling_vol > 0, df['Volume'] / rolling_vol, 1.0)
        df['Stock_Return_10d'] = df['Close'] / df['Close'].shift(10) - 1
        df['Relative_Strength_10d'] = df['Stock_Return_10d'] - df['Nifty_Return_10d']
        
        latest_row = df.iloc[-1:][FEATURE_COLS].dropna()
        if not latest_row.empty:
            live_rows.append(latest_row)
            valid_tickers.append(ticker)
            last_prices.append(round(latest_close, 2))
    except Exception:
        pass

# FIX: Check if list is empty before attempting concatenation
if not live_rows:
    print("\n❌ Error: No valid stocks passed the filters today.")
    print("This usually happens if the market has been closed for many days, or the API returned blank data.")
    exit()

X_live = pd.concat(live_rows)

# --- 5. INFERENCE & PERCENTILE RANKING ---
raw_predictions = bst.predict(X_live)

percentiles = pd.Series(raw_predictions).rank(pct=True) * 100

results_df = pd.DataFrame({
    'Ticker': valid_tickers,
    'LTP': last_prices,
    'Win_Probability': raw_predictions,
    'Percentile_Rank': percentiles
}).sort_values(by='Percentile_Rank', ascending=False)

top_10 = results_df.head(10)

# Save to daily CSV log
today_str = datetime.today().strftime('%Y-%m-%d')
log_filename = f"signals_{today_str}.csv"
top_10.to_csv(log_filename, index=False)

print("\n" + "="*70)
print(f"🎯 TOP 10 HIGH-CONVICTION TRADE CANDIDATES ({today_str})")
print("="*70)
print(f"{'Ticker':<15} | {'LTP (₹)':<10} | {'Win Prob':<10} | {'Percentile':<12}")
print("-"*70)
for _, row in top_10.iterrows():
    print(f"{row['Ticker']:<15} | {row['LTP']:<10.2f} | {row['Win_Probability']*100:<9.2f}% | Top {100 - row['Percentile_Rank']:<5.1f}%")
print("="*70)
print(f" Daily signals saved locally to '{log_filename}'\n")