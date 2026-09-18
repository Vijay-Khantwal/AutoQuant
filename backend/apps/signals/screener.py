import logging
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

def is_fundamentally_sound(ticker: str) -> bool:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # 1. Market Cap > 5,000 Cr (50,000,000,000 INR)
        mcap = info.get("marketCap", 0)
        if mcap and mcap < 50_000_000_000:
            return False
            
        # 2. Free Cash Flow > 0
        fcf = info.get("freeCashflow", None)
        if fcf is None:
            # Fallback to cashflow statement
            try:
                cf = t.cashflow
                if not cf.empty and "Free Cash Flow" in cf.index:
                    latest_fcf = cf.loc["Free Cash Flow"].iloc[0]
                    import pandas as pd
                    if pd.notna(latest_fcf):
                        fcf = float(latest_fcf)
            except Exception:
                pass

        if fcf is not None and fcf < 0:
            return False
            
        # 3. Debt-to-Equity < 1.5
        dte = info.get("debtToEquity", None)
        if dte is not None and dte > 150.0:
            return False
            
        return True
    except Exception as e:
        return True

def pre_ml_screen(tickers: list[str], log_callback=None) -> list[str]:
    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)
            
    log(f"Running fundamental Pre-ML Screener on {len(tickers)} stocks...")
    valid_tickers = []
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(lambda t: (t, is_fundamentally_sound(t)), tickers)
        for t, is_sound in results:
            if is_sound:
                valid_tickers.append(t)
                
    dropped = len(tickers) - len(valid_tickers)
    log(f"Pre-ML Screener complete. Dropped {dropped} fundamentally weak stocks. {len(valid_tickers)} remaining.")
    return valid_tickers
