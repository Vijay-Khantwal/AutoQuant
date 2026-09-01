import yfinance as yf
from niftystocks import ns
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import precision_score
import logging
import warnings
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & SCHEMA LOCK ---
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

HOLD_PERIOD = 15      # Forward trading days
TP_TARGET = 0.03      # +3% Take-Profit
SL_STOP = -0.02       # -2% Stop-Loss
MIN_PRICE = 50.0      # Reject penny stocks
MIN_VOLUME = 100000   # Reject illiquid stocks
CACHE_FILE = 'nifty500_train_cache.pkl'

FEATURE_COLS = [
    'Intraday_Range', 'Close_Open_Momentum', 'Top_Wick_Rejection',
    'Dist_SMA_10', 'Dist_SMA_50', 'Volume_Ratio',
    'Relative_Strength_10d', 'Market_Regime_200'
]

# Dynamic Date Boundaries: 2018 to (Today - 25 days)
START_DATE = '2018-01-01'
END_DATE = (datetime.today() - timedelta(days=25)).strftime('%Y-%m-%d')

# --- 2. CACHED DATA INGESTION ---
print(f"Dataset Window: {START_DATE} to {END_DATE}")

if os.path.exists(CACHE_FILE):
    print("⚡ Loading data from local cache...")
    raw_data = pd.read_pickle(CACHE_FILE)
    nifty_df = yf.Ticker('^NSEI').history(start=START_DATE, end=END_DATE)
else:
    print("📥 Fetching Nifty 500 universe from Yahoo Finance... (Takes ~1 min)")
    raw_basket = ns.get_nifty500_with_ns()
    known_delisted = ['HDFC.NS', 'TATAMOTORS.NS', 'MOTHERSUMI.NS', 'MINDAIND.NS', 'IBULHSGFIN.NS']
    stock_basket = [t for t in raw_basket if t not in known_delisted]
    
    raw_data = yf.download(stock_basket, start=START_DATE, end=END_DATE, progress=False, threads=True, group_by='ticker')
    nifty_df = yf.Ticker('^NSEI').history(start=START_DATE, end=END_DATE)
    
    raw_data.to_pickle(CACHE_FILE)
    print(f" Saved cache locally to {CACHE_FILE}")

# Process Macro Benchmark
nifty_df['Nifty_SMA_200'] = nifty_df['Close'].rolling(window=200).mean()
nifty_df['Market_Regime_200'] = nifty_df['Close'] / nifty_df['Nifty_SMA_200'] - 1
nifty_df['Nifty_Return_10d'] = nifty_df['Close'] / nifty_df['Close'].shift(10) - 1
macro_features = nifty_df[['Market_Regime_200', 'Nifty_Return_10d']].copy().tz_localize(None)

# --- 3. VECTORIZED LABELING & FEATURE ENGINEERING ---
def create_path_dependent_labels(highs, lows, closes, hold_days, tp, sl):
    n = len(closes)
    labels = np.zeros(n)
    for i in range(n - hold_days):
        entry = closes[i]
        tp_price, sl_price = entry * (1 + tp), entry * (1 + sl)
        hit_tp = False
        for j in range(1, hold_days + 1):
            if lows[i + j] <= sl_price:
                hit_tp = False
                break
            if highs[i + j] >= tp_price:
                hit_tp = True
                break
        labels[i] = 1 if hit_tp else 0
    return labels

print("Processing features and applying path-dependent labeling...")
all_stock_data = []
available_tickers = list(set([col[0] for col in raw_data.columns]))

for ticker_symbol in available_tickers:
    try:
        df = raw_data[ticker_symbol].copy()
        if df['Close'].isna().all() or len(df.dropna()) < 250:
            continue
            
        # Hard filters: Penny stock and volume
        if df['Close'].iloc[-1] < MIN_PRICE or df['Volume'].rolling(20).mean().iloc[-1] < MIN_VOLUME:
            continue
            
        df.index = df.index.tz_localize(None)
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
        
        df['Target'] = create_path_dependent_labels(
            df['High'].values, df['Low'].values, df['Close'].values, 
            HOLD_PERIOD, TP_TARGET, SL_STOP
        )
        df['Ticker'] = ticker_symbol
        df = df.iloc[:-HOLD_PERIOD].dropna()
        all_stock_data.append(df)
    except Exception:
        pass

dataset = pd.concat(all_stock_data).sort_index()
X, y = dataset[FEATURE_COLS], dataset['Target']
print(f"Clean Training Samples: {len(dataset):,} across {len(all_stock_data)} valid stocks.")

# --- 4. WALK-FORWARD VALIDATION ---
print("\n--- Walk-Forward Validation (Top 5% Conviction) ---")
unique_dates = np.array(sorted(dataset.index.unique()))
split_size = len(unique_dates) // 4

for fold in range(1, 4):
    train_end = split_size * fold
    test_end = split_size * (fold + 1)
    train_mask = dataset.index.isin(unique_dates[:train_end])
    test_mask = dataset.index.isin(unique_dates[train_end:test_end])
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    clf = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, max_depth=4, subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
    clf.fit(X_train, y_train)
    probs = clf.predict_proba(X_test)[:, 1]
    
    top_5_threshold = np.percentile(probs, 95)
    selected_trades = probs >= top_5_threshold
    
    if np.sum(selected_trades) > 0:
        base_rate = y_test.mean() * 100
        model_prec = precision_score(y_test[selected_trades], (probs[selected_trades] >= top_5_threshold).astype(int)) * 100
        print(f"Fold {fold} ({pd.to_datetime(unique_dates[train_end]).date()} to {pd.to_datetime(unique_dates[test_end-1]).date()}):")
        print(f"  Base Rate: {base_rate:.1f}% | Model Top 5%: {model_prec:.1f}% | Edge: +{model_prec - base_rate:.1f}%\n")

# --- 5. EXPORT FINAL PRODUCTION MODEL ---
print("Training Final Model on all data...")
production_model = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, max_depth=4, subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
production_model.fit(X, y)
production_model.booster_.save_model('nifty500_model.txt')
print(" Production model exported to 'nifty500_model.txt'")