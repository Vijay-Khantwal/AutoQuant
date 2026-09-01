import pandas as pd
import requests
import os

SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
LOCAL_CACHE = "dhan_scrip_master.csv"

def download_and_load_scrip_master() -> pd.DataFrame:
    """Downloads the latest Dhan Scrip Master CSV or loads from local cache."""
    if not os.path.exists(LOCAL_CACHE):
        print("📥 Downloading latest Scrip Master from DhanHQ...")
        response = requests.get(SCRIP_MASTER_URL)
        response.raise_for_status()
        
        with open(LOCAL_CACHE, "wb") as f:
            f.write(response.content)
            
    # Load into Pandas dataframe
    df = pd.read_csv(LOCAL_CACHE, low_memory=False)
    
    # Clean column headers of any hidden whitespaces
    df.columns = df.columns.str.strip()
    return df

def get_dhan_security_id(yahoo_ticker: str) -> str:
    """
    Translates a Yahoo Finance ticker (e.g., 'PIDILITIND.NS') 
    to a Dhan NSE Equity Security ID (e.g., '11262').
    """
    clean_symbol = yahoo_ticker.replace('.NS', '').replace('.BO', '').strip()
    df = download_and_load_scrip_master()
    
    # Strip hidden spaces from Dhan's data columns to ensure a match
    columns_to_clean = ['SEM_EXM_EXCH_ID', 'SEM_SERIES', 'SEM_TRADING_SYMBOL', 'SM_SYMBOL_NAME', 'SEM_CUSTOM_SYMBOL']
    for col in columns_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    nse_df = df[df['SEM_EXM_EXCH_ID'] == 'NSE']
    
    match = nse_df[
        (nse_df['SEM_TRADING_SYMBOL'] == clean_symbol) | 
        (nse_df['SM_SYMBOL_NAME'] == clean_symbol) | 
        (nse_df['SEM_CUSTOM_SYMBOL'] == clean_symbol)
    ]
    
    if not match.empty:
        eq_match = match[match['SEM_SERIES'] == 'EQ']
        final_match = eq_match if not eq_match.empty else match
        
        # Dhan's Security ID column name (Usually SEM_SMST_SECURITY_ID)
        possible_id_cols = ['SEM_SMST_SECURITY_ID', 'SECURITY_ID', 'SEM_SECURITY_ID']
        
        for col in possible_id_cols:
            if col in final_match.columns:
                return str(final_match[col].values[0])
                
        # If it completely fails, print available columns for easy debugging
        print(f"Available columns in CSV: {list(final_match.columns)}")
        raise ValueError("Could not find the exact Security ID column in the Dhan CSV.")
    else:
        raise ValueError(f"Ticker '{clean_symbol}' not found in Dhan NSE Equity master list.")