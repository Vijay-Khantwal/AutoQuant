import os
import json
import glob
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from tools.web_search import TavilyProvider, SerperJinaProvider, tool_deep_web_research
from tools.fundamentals import tool_deep_fundamentals
from dotenv import load_dotenv
load_dotenv()

# Automatically reads TAVILY_API_KEY from .env:
search_engine = TavilyProvider()

# If you want to switch to Serper later, just change to:
# search_engine = SerperJinaProvider()

# --- 1. CONFIGURE SEARCH PROVIDER (SWAPPABLE HERE) ---
# To switch to Serper+Jina, just change this one line:
# search_engine = SerperJinaProvider(serper_api_key="YOUR_SERPER_KEY")


# --- 2. LOAD LATEST SIGNALS CSV ---
signal_files = glob.glob("signals_*.csv")
if not signal_files:
    print("No signal files found. Run predict.py first.")
    exit()

latest_file = sorted(signal_files)[-1]
print(f"📄 Loading signals from: {latest_file}")
signals_df = pd.read_csv(latest_file)

# We analyze the Top 3 candidates
top_candidates = signals_df.head(3)

# --- 3. EXECUTE DEEP RESEARCH PIPELINE ---
def process_single_stock(row):
    ticker = row['Ticker']
    ltp = row['LTP']
    prob = row['Win_Probability']
    pct = row['Percentile_Rank']
    
    print(f"🔍 Researching {ticker} (LTP: ₹{ltp}, Prob: {prob*100:.1f}%)...")
    
    # Tool 1: Balance Sheet & Profitability
    fund_data = tool_deep_fundamentals(ticker)
    
    # Tool 2: Deep Web Articles & Sentiment
    web_data = tool_deep_web_research(ticker, provider=search_engine)
    
    # Assemble Unified Exhaustive JSON
    structured_dossier = {
        "metadata": {
            "ticker": ticker,
            "research_timestamp": datetime.now().isoformat(),
            "execution_mode": "AUTONOMOUS_PAPER_TRADING"
        },
        "quantitative_inputs": {
            "ltp": ltp,
            "ml_win_probability": prob,
            "percentile_rank": pct,
            "target_tp_pct": 3.0,
            "target_sl_pct": -2.0
        },
        "fundamentals": fund_data,
        "deep_web_research": web_data
    }
    return structured_dossier

print(f"\n🚀 Running Deep Multi-Tool Research on Top {len(top_candidates)} Stocks...")

# Parallel execution across all candidate stocks
dossiers = []
with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(process_single_stock, [row for _, row in top_candidates.iterrows()])
    dossiers = list(results)

# --- 4. EXPORT COMPILED RESEARCH DOSSIER ---
output_json_path = f"dossier_{datetime.today().strftime('%Y-%m-%d')}.json"
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(dossiers, f, indent=2)

print(f"\n✅ Research completed! Full JSON dossier saved to '{output_json_path}'.")