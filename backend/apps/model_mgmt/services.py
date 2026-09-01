"""
model_mgmt/services.py
LightGBM training pipeline — refactored train.py as importable service.
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yfinance as yf
from niftystocks import ns
from sklearn.metrics import precision_score

from django.conf import settings

logger = logging.getLogger(__name__)

MIN_PRICE   = 50.0
MIN_VOLUME  = 100_000

FEATURE_COLS = [
    "Intraday_Range", "Close_Open_Momentum", "Top_Wick_Rejection",
    "Dist_SMA_10", "Dist_SMA_50", "Volume_Ratio",
    "Relative_Strength_10d", "Market_Regime_200",
]

TRADING_ROOT = Path(settings.TRADING_ROOT)
CACHE_FILE = settings.DATA_DIR / "nifty500_train_cache.pkl"

START_DATE = "2018-01-01"


def _create_labels(highs, lows, closes, hold_days, tp, sl):
    n = len(closes)
    labels = np.zeros(n)
    for i in range(n - hold_days):
        entry = closes[i]
        tp_price, sl_price = entry * (1 + tp), entry * (1 + sl)
        hit_tp = False
        for j in range(1, hold_days + 1):
            if lows[i + j] <= sl_price:
                break
            if highs[i + j] >= tp_price:
                hit_tp = True
                break
        labels[i] = 1 if hit_tp else 0
    return labels


def retrain_model(strategy_id: int, log_callback=None) -> dict:
    """
    Full LightGBM retraining pipeline for a specific strategy profile.
    Returns metrics dict. log_callback(str) is called for each progress line.
    """
    from .models import StrategyProfile
    strategy = StrategyProfile.objects.get(id=strategy_id)
    hold_period = strategy.hold_days
    tp_target = strategy.tp_target
    sl_stop = strategy.sl_stop

    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    log(f"Started training {strategy.name} (TP: {tp_target}, SL: {sl_stop}, Hold: {hold_period}d)")

    end_date = (datetime.today() - timedelta(days=hold_period + 10)).strftime("%Y-%m-%d")
    log(f"Dataset window: {START_DATE} → {end_date}")

    if CACHE_FILE.exists():
        log("⚡ Loading from local training cache...")
        raw_data = pd.read_pickle(str(CACHE_FILE))
        nifty_df = yf.Ticker("^NSEI").history(start=START_DATE, end=end_date)
    else:
        log("📥 Fetching Nifty 500 universe (this takes ~2 minutes)...")
        raw_basket = ns.get_nifty500_with_ns()
        known_delisted = ["HDFC.NS", "TATAMOTORS.NS", "MOTHERSUMI.NS", "MINDAIND.NS", "IBULHSGFIN.NS"]
        stock_basket = [t for t in raw_basket if t not in known_delisted]
        raw_data = yf.download(stock_basket, start=START_DATE, end=end_date, progress=False, threads=True, group_by="ticker")
        nifty_df = yf.Ticker("^NSEI").history(start=START_DATE, end=end_date)
        raw_data.to_pickle(str(CACHE_FILE))
        log(f"Cache saved → {CACHE_FILE}")

    nifty_df["Nifty_SMA_200"] = nifty_df["Close"].rolling(window=200).mean()
    nifty_df["Market_Regime_200"] = nifty_df["Close"] / nifty_df["Nifty_SMA_200"] - 1
    nifty_df["Nifty_Return_10d"] = nifty_df["Close"] / nifty_df["Close"].shift(10) - 1
    macro_features = nifty_df[["Market_Regime_200", "Nifty_Return_10d"]].copy().tz_localize(None)

    log("Processing features and applying path-dependent labelling...")
    all_stock_data = []
    available_tickers = list({col[0] for col in raw_data.columns})

    for sym in available_tickers:
        try:
            df = raw_data[sym].copy()
            if df["Close"].isna().all() or len(df.dropna()) < 250:
                continue
            if df["Close"].iloc[-1] < MIN_PRICE or df["Volume"].rolling(20).mean().iloc[-1] < MIN_VOLUME:
                continue
            df.index = df.index.tz_localize(None)
            df = df.join(macro_features, how="inner")
            df["Intraday_Range"] = (df["High"] - df["Low"]) / df["Open"]
            df["Close_Open_Momentum"] = (df["Close"] - df["Open"]) / df["Open"]
            df["Top_Wick_Rejection"] = (df["High"] - df[["Open", "Close"]].max(axis=1)) / df["Open"]
            df["SMA_10"] = df["Close"].rolling(10).mean()
            df["SMA_50"] = df["Close"].rolling(50).mean()
            df["Dist_SMA_10"] = df["Close"] / df["SMA_10"] - 1
            df["Dist_SMA_50"] = df["Close"] / df["SMA_50"] - 1
            rv = df["Volume"].rolling(20).mean()
            df["Volume_Ratio"] = np.where(rv > 0, df["Volume"] / rv, 1.0)
            df["Stock_Return_10d"] = df["Close"] / df["Close"].shift(10) - 1
            df["Relative_Strength_10d"] = df["Stock_Return_10d"] - df["Nifty_Return_10d"]
            df["Target"] = _create_labels(df["High"].values, df["Low"].values, df["Close"].values, hold_period, tp_target, sl_stop)
            df["Ticker"] = sym
            df = df.iloc[:-hold_period].dropna()
            all_stock_data.append(df)
        except Exception:
            pass

    dataset = pd.concat(all_stock_data).sort_index()
    X, y = dataset[FEATURE_COLS], dataset["Target"]
    log(f"Clean samples: {len(dataset):,} across {len(all_stock_data)} stocks.")

    # Walk-forward validation
    log("--- Walk-Forward Validation ---")
    unique_dates = np.array(sorted(dataset.index.unique()))
    split_size = len(unique_dates) // 4
    fold_metrics = []

    for fold in range(1, 4):
        train_end = split_size * fold
        test_end = split_size * (fold + 1)
        train_mask = dataset.index.isin(unique_dates[:train_end])
        test_mask = dataset.index.isin(unique_dates[train_end:test_end])
        X_tr, y_tr = X[train_mask], y[train_mask]
        X_te, y_te = X[test_mask], y[test_mask]
        clf = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, max_depth=4, subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
        clf.fit(X_tr, y_tr)
        probs = clf.predict_proba(X_te)[:, 1]
        threshold = np.percentile(probs, 95)
        selected = probs >= threshold
        if np.sum(selected) > 0:
            base_rate = float(y_te.mean() * 100)
            precision = float(precision_score(y_te[selected], (probs[selected] >= threshold).astype(int)) * 100)
            log(f"Fold {fold}: Base Rate={base_rate:.1f}% | Top-5% Precision={precision:.1f}% | Edge=+{precision - base_rate:.1f}%")
            fold_metrics.append({"fold": fold, "base_rate": base_rate, "precision": precision})

    log("Training final production model on all data...")
    final_model = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, max_depth=4, subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
    final_model.fit(X, y)
    
    model_path = os.path.join(settings.DATA_DIR, f"model_strategy_{strategy_id}.txt")
    log(f"Saving final model to {model_path}...")
    final_model.booster_.save_model(str(model_path))
    log(f"✅ Production model saved → {model_path}")

    # Feature importances
    importances = dict(zip(FEATURE_COLS, final_model.feature_importances_.tolist()))

    return {
        "fold_metrics": fold_metrics,
        "feature_importances": importances,
        "total_samples": len(dataset),
        "total_stocks": len(all_stock_data),
        "model_path": str(model_path),
    }
