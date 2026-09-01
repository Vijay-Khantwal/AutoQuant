import os
import glob
import json
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from openai import OpenAI

# Load API keys from .env
load_dotenv()

from tools.fundamentals import tool_deep_fundamentals
from tools.web_search import TavilyProvider, tool_deep_web_research

# --- 1. CONFIGURATION & CLIENT INITIALIZATION ---
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
WORKER_MODEL = os.getenv("WORKER_MODEL", "stepfun-ai/step-3.7-flash")
AUDITOR_MODEL = os.getenv("AUDITOR_MODEL", "nvidia/nemotron-3-super-120b-a12b")

nvidia_key = os.getenv("NVIDIA_API_KEY")
if not nvidia_key:
    raise ValueError("NVIDIA API Key missing. Please set NVIDIA_API_KEY in .env")

# Initialize OpenAI client pointing to NVIDIA NIM (handles both models natively)
nim_client = OpenAI(base_url=NIM_BASE_URL, api_key=nvidia_key)
search_engine = TavilyProvider()

# --- 2. TIER 1: THE WORKER (StepFun 3.7 Flash - News Distiller) ---
def distill_news_articles(ticker: str, web_data: dict) -> str:
    """Tier 1 LLM: Reads noisy raw articles and extracts hard facts at blazing speed."""
    articles = web_data.get('articles', [])
    if not articles:
        return "No recent news articles found."
        
    raw_text_dump = "\n\n---\n\n".join(
        [f"Title: {a['title']}\nContent: {a['content'][:3000]}" for a in articles]
    )
    
    prompt = f"""
    You are a fast financial data distiller. Read the following recent articles for {ticker}.
    Extract ONLY the concrete facts affecting the stock. Ignore fluff.
    
    Provide a concise bulleted list covering:
    1. Regulatory/Legal Risks (SEBI probes, lawsuits, fraud).
    2. Management/Earnings Guidance (Upcoming results, margin outlooks).
    3. General Market Sentiment (Broker upgrades/downgrades).
    
    Raw Articles:
    {raw_text_dump}
    """
    
    try:
        response = nim_client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Worker Extraction Failed: {str(e)}"

# --- 3. TIER 2: THE AUDITOR (Nemotron 3 Super 120B - Chief Risk Officer) ---
SYSTEM_INSTRUCTION = """
You are a Senior Quantitative Equity Risk Officer for the Indian Stock Market (NSE).
Your task is to conduct a strict risk audit on a candidate swing trade.

Hard Veto Rules (Reject immediately if any are true):
1. Insolvency Risk: Debt-to-Equity > 2.0 (except Banks/NBFCs).
2. Negative Cash Flows: Negative operating cash flow coupled with high debt.
3. Severe Governance / Regulatory Hazards: Active SEBI investigations, fraud, or promoter insider controversies mentioned in the news.

Decision Standard:
- APPROVE: If no hard veto triggers apply and fundamentals/sentiment support stability.
- REJECT: If any governance, solvency, or event risk threatens a 15-day hold period.

You MUST respond ONLY with a valid JSON object matching the requested schema. Do NOT wrap it in markdown blockquotes (e.g., no ```json).
"""

def generate_auditor_prompt(dossier: dict, news_brief: str) -> str:
    return f"""
Evaluate the following equity dossier and output your final audit verdict.

=== CANDIDATE DOSSIER ===
Ticker: {dossier['metadata']['ticker']}
LTP: ₹{dossier['quantitative_inputs']['ltp']}
ML Win Probability: {dossier['quantitative_inputs']['ml_win_probability']*100:.2f}%
Percentile Rank: Top {100 - dossier['quantitative_inputs']['percentile_rank']:.1f}%

--- FUNDAMENTALS & VALUATION ---
{json.dumps(dossier['fundamentals'], indent=2)}

--- TIER 1 NEWS BRIEF (DISTILLED FACTS) ---
{news_brief}

Output your evaluation strictly in the following JSON format:
{{
  "ticker": "{dossier['metadata']['ticker']}",
  "decision": "APPROVE" or "REJECT",
  "confidence_score": 0.00,
  "risk_flags": [
    "<string explaining flag, or empty if none>"
  ],
  "fundamental_summary": "<brief assessment of debt, cashflow, and valuation>",
  "news_and_sentiment_summary": "<brief synthesis of the news brief>",
  "final_rationale": "<concise 2-sentence rationale for approval or rejection>",
  "recommended_allocation_inr": <number: 0 if REJECT, up to 20000 if APPROVE>
}}
"""

# --- 4. EXECUTION PIPELINE ---
def process_full_audit(row: pd.Series) -> dict:
    ticker = row['Ticker']
    ltp = row['LTP']
    prob = row['Win_Probability']
    pct = row['Percentile_Rank']
    
    print(f"\n[1/3] 🔍 {ticker}: Gathering tools data...")
    fund_data = tool_deep_fundamentals(ticker)
    web_data = tool_deep_web_research(ticker, provider=search_engine)
    
    dossier = {
        "metadata": {"ticker": ticker, "research_timestamp": datetime.now().isoformat()},
        "quantitative_inputs": {"ltp": ltp, "ml_win_probability": prob, "percentile_rank": pct},
        "fundamentals": fund_data
    }
    
    print(f"[2/3] ⚙️ {ticker}: Tier 1 Worker (StepFun-3.7-Flash) distilling news...")
    news_brief = distill_news_articles(ticker, web_data)
    
    print(f"[3/3] ⚖️ {ticker}: Tier 2 Auditor (Nemotron-120B) generating JSON verdict...")
    prompt = generate_auditor_prompt(dossier, news_brief)
    
    try:
        response = nim_client.chat.completions.create(
            model=AUDITOR_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024,
            # Force JSON-only output by disabling the internal thinking stream
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        
        raw_output = response.choices[0].message.content.strip()
        clean_json_str = raw_output.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        
        verdict = json.loads(clean_json_str)
        return {**dossier, "news_brief": news_brief, "audit_verdict": verdict}
    except Exception as e:
        print(f"❌ {ticker} Auditor Error: {str(e)}")
        return {
            **dossier, "news_brief": news_brief,
            "audit_verdict": {
                "ticker": ticker, "decision": "REJECT", "confidence_score": 0.0,
                "risk_flags": [f"LLM Parsing Error: {str(e)}"],
                "final_rationale": "Audit failed due to JSON decoding error.",
                "recommended_allocation_inr": 0
            }
        }

def main():
    signal_files = glob.glob("signals_*.csv")
    if not signal_files:
        print("❌ No signal files found. Run predict.py first.")
        return

    latest_signal_file = sorted(signal_files)[-1]
    print(f"📄 Loading latest market signals: {latest_signal_file}")
    signals_df = pd.read_csv(latest_signal_file)
    
    candidates = signals_df.head(3)
    print(f"\n🚀 Launching Two-Tier Autonomous Agent on Top {len(candidates)} Candidates...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        completed_audits = list(executor.map(process_full_audit, [row for _, row in candidates.iterrows()]))
        
    today_str = datetime.today().strftime('%Y-%m-%d')
    output_filename = f"decisions_{today_str}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(completed_audits, f, indent=2)
        
    print("\n" + "="*90)
    print(f"📋 AUTONOMOUS AGENT AUDIT SUMMARY ({today_str})")
    print("="*90)
    print(f"{'Ticker':<15} | {'Decision':<10} | {'Confidence':<12} | {'Risk Flags':<15} | {'Allocation'}")
    print("-" * 90)
    
    for item in completed_audits:
        v = item['audit_verdict']
        flags_count = len(v.get('risk_flags', []))
        flag_str = f"{flags_count} flag(s)" if flags_count > 0 else "Clean"
        alloc_str = f"₹{v.get('recommended_allocation_inr', 0):,}"
        print(f"{v['ticker']:<15} | {v['decision']:<10} | {v['confidence_score']*100:<10.1f}% | {flag_str:<15} | {alloc_str}")
        print(f"  ↳ Rationale: {v.get('final_rationale')}\n")
        
    print("="*90)
    print(f"✅ Full audit dossier saved to '{output_filename}'\n")

if __name__ == "__main__":
    main()