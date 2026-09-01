"""
execution/services/dhan_mapper.py
Downloads and parses Dhan Scrip Master to map Yahoo tickers to Dhan Security IDs.
"""
import logging
import os
from pathlib import Path
import pandas as pd
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
_scrip_df: pd.DataFrame = None


def load_scrip_master(force_refresh: bool = False) -> pd.DataFrame:
    global _scrip_df
    if _scrip_df is not None and not force_refresh:
        return _scrip_df

    local_cache = Path(os.path.join(settings.DATA_DIR, "dhan_scrip_master.csv"))

    if not local_cache.exists() or force_refresh:
        logger.info("Downloading latest Dhan Scrip Master CSV...")
        response = requests.get(SCRIP_MASTER_URL, timeout=60)
        response.raise_for_status()
        local_cache.write_bytes(response.content)

    df = pd.read_csv(str(local_cache), low_memory=False)
    df.columns = df.columns.str.strip()

    cols_to_clean = ["SEM_EXM_EXCH_ID", "SEM_SERIES", "SEM_TRADING_SYMBOL",
                     "SM_SYMBOL_NAME", "SEM_CUSTOM_SYMBOL"]
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    _scrip_df = df
    return _scrip_df


def get_dhan_security_id(yahoo_ticker: str, force_refresh: bool = False) -> str:
    clean_symbol = yahoo_ticker.replace(".NS", "").replace(".BO", "").strip()
    df = load_scrip_master(force_refresh=force_refresh)

    nse_df = df[df["SEM_EXM_EXCH_ID"] == "NSE"]
    match = nse_df[
        (nse_df["SEM_TRADING_SYMBOL"] == clean_symbol) |
        (nse_df["SM_SYMBOL_NAME"] == clean_symbol) |
        (nse_df["SEM_CUSTOM_SYMBOL"] == clean_symbol)
    ]

    if match.empty:
        raise ValueError(f"Ticker '{clean_symbol}' not found in Dhan NSE Equity master.")

    eq_match = match[match["SEM_SERIES"] == "EQ"]
    final_match = eq_match if not eq_match.empty else match

    for col in ["SEM_SMST_SECURITY_ID", "SECURITY_ID", "SEM_SECURITY_ID"]:
        if col in final_match.columns:
            return str(final_match[col].values[0])

    raise ValueError(f"Security ID column not found. Available: {list(final_match.columns)}")

