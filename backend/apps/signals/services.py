"""
signals/services.py — Real ML prediction pipeline
"""
import logging
import warnings
import os
from datetime import datetime, timedelta

import lightgbm as lgb
import numpy as np
import pandas as pd
import yfinance as yf
from niftystocks import ns

from django.conf import settings

logger = logging.getLogger(__name__)

logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

MIN_PRICE = 50.0
MIN_VOLUME = 100_000
MAX_STALE_DAYS = 6
FEATURE_COLS = [
    "Intraday_Range", "Close_Open_Momentum", "Top_Wick_Rejection",
    "Dist_SMA_10", "Dist_SMA_50", "Volume_Ratio",
    "Relative_Strength_10d", "Market_Regime_200",
]


def load_model(strategy_id: int) -> lgb.Booster:
    model_path = os.path.join(settings.DATA_DIR, f"model_strategy_{strategy_id}.txt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Run retrain first.")
    return lgb.Booster(model_file=str(model_path))


def run_prediction(strategy_id: int, log_callback=None) -> list[dict]:
    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    log("Loading LightGBM model...")
    model = load_model(strategy_id)

    log("Fetching live market snapshot from Yahoo Finance...")
    raw_basket = ns.get_nifty500_with_ns()
    known_delisted = ["HDFC.NS", "TATAMOTORS.NS", "MOTHERSUMI.NS", "MINDAIND.NS", "IBULHSGFIN.NS"]
    stock_basket = [t for t in raw_basket if t not in known_delisted]

    # Fetch 210 days to cover 200-SMA + 10-day return
    start_date = (datetime.today() - timedelta(days=320)).strftime("%Y-%m-%d")
    raw_data = yf.download(stock_basket, start=start_date, progress=False, threads=True, group_by="ticker")
    nifty_df = yf.Ticker("^NSEI").history(start=start_date)

    if nifty_df.empty:
        raise ValueError("Failed to fetch Nifty index data.")

    log("Extracting features and running inferences...")
    nifty_df["Nifty_SMA_200"] = nifty_df["Close"].rolling(window=200).mean()
    nifty_df["Market_Regime_200"] = nifty_df["Close"] / nifty_df["Nifty_SMA_200"] - 1
    nifty_df["Nifty_Return_10d"] = nifty_df["Close"] / nifty_df["Close"].shift(10) - 1
    macro_features = nifty_df[["Market_Regime_200", "Nifty_Return_10d"]].copy().tz_localize(None)

    available_tickers = list({col[0] for col in raw_data.columns})
    inference_rows = []

    for sym in available_tickers:
        try:
            df = raw_data[sym].copy()
            if df.empty or df["Close"].isna().all():
                continue
            
            df = df.dropna()
            if len(df) < 200:
                continue

            # Check stale data
            last_date = df.index[-1].tz_localize(None)
            stale_days = (datetime.today() - last_date).days
            if stale_days > MAX_STALE_DAYS:
                continue

            last_price = float(df["Close"].iloc[-1])
            last_vol = float(df["Volume"].rolling(20).mean().iloc[-1])
            if pd.isna(last_price) or pd.isna(last_vol):
                # logger.warning(f"{sym} skipped: NaN price or volume")
                continue
            if last_price < MIN_PRICE or last_vol < MIN_VOLUME:
                # logger.warning(f"{sym} skipped: Price {last_price} < {MIN_PRICE} or Vol {last_vol} < {MIN_VOLUME}")
                continue

            df.index = df.index.tz_localize(None)
            df = df.join(macro_features, how="inner")
            
            row = df.iloc[-1]
            features = {
                "Intraday_Range": (row["High"] - row["Low"]) / row["Open"],
                "Close_Open_Momentum": (row["Close"] - row["Open"]) / row["Open"],
                "Top_Wick_Rejection": (row["High"] - max(row["Open"], row["Close"])) / row["Open"],
                "Dist_SMA_10": row["Close"] / df["Close"].rolling(10).mean().iloc[-1] - 1,
                "Dist_SMA_50": row["Close"] / df["Close"].rolling(50).mean().iloc[-1] - 1,
                "Volume_Ratio": row["Volume"] / last_vol if last_vol > 0 else 1.0,
                "Relative_Strength_10d": (row["Close"] / df["Close"].shift(10).iloc[-1] - 1) - row["Nifty_Return_10d"],
                "Market_Regime_200": row["Market_Regime_200"]
            }
            features["ticker"] = sym
            features["ltp"] = last_price
            inference_rows.append(features)
        except Exception as e:
            print(f"Error processing {sym}: {e}")
            continue

    if not inference_rows:
        raise ValueError("No valid tickers found for inference.")

    pred_df = pd.DataFrame(inference_rows)
    X = pred_df[FEATURE_COLS]
    
    log(f"Predicting on {len(pred_df)} valid candidates...")
    probs = model.predict(X)
    pred_df["Win_Prob"] = probs

    top_n = settings.TOP_N_CANDIDATES
    top_candidates = pred_df.sort_values(by="Win_Prob", ascending=False).head(top_n)

    candidates = []
    total_valid = len(pred_df)
    
    for i, (_, row) in enumerate(top_candidates.iterrows()):
        candidates.append({
            "ticker": row["ticker"],
            "ltp": round(row["ltp"], 2),
            "win_probability": round(row["Win_Prob"], 4),
            "percentile_rank": round(100.0 * (1 - (i / total_valid)), 2),
            "rank": i + 1
        })

    log(f"Prediction complete. Top {top_n} candidates selected.")
    return candidates

