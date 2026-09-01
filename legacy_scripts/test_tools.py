import json
from dotenv import load_dotenv

# Load .env keys first
load_dotenv()

from tools.fundamentals import tool_deep_fundamentals
from tools.web_search import TavilyProvider, SerperJinaProvider, tool_deep_web_research

TEST_TICKER = "ICICIBANK.NS"

def test_fundamentals():
    print("\n" + "="*60)
    print(f"🧪 [1/2] TESTING: tool_deep_fundamentals ('{TEST_TICKER}')")
    print("="*60)
    
    result = tool_deep_fundamentals(TEST_TICKER)
    
    if result.get("status") == "SUCCESS":
        print("✅ Fundamentals Tool: PASSED")
        print(f"  • P/E Ratio        : {result['valuation']['pe_ratio']}")
        print(f"  • Debt-to-Equity   : {result['solvency']['debt_to_equity']}")
        print(f"  • Return on Equity : {result['profitability_and_returns']['roe_pct']}%")
        print(f"  • Operating Cashflow: ₹{result['profitability_and_returns']['operating_cash_flow_inr']:,}")
    else:
        print("❌ Fundamentals Tool: FAILED")
        print(f"  Error message: {result.get('message')}")
        
    return result

def test_web_search_tavily():
    print("\n" + "="*60)
    print(f"🧪 [2/2] TESTING: tool_deep_web_research via Tavily ('{TEST_TICKER}')")
    print("="*60)
    
    try:
        provider = TavilyProvider() # Reads TAVILY_API_KEY from .env
        result = tool_deep_web_research(TEST_TICKER, provider=provider)
        
        sources_count = result.get("total_sources_analyzed", 0)
        articles = result.get("articles", [])
        
        if sources_count > 0 and len(articles) > 0 and "Error" not in articles[0]['title']:
            print("✅ Tavily Search Tool: PASSED")
            print(f"  • Total Articles Fetched: {sources_count}")
            print(f"  • Sample Headline       : {articles[0]['title']}")
            print(f"  • Content Snippet Length: {len(articles[0]['content'])} characters")
        else:
            print("❌ Tavily Search Tool: FAILED (Empty or Error output)")
            print(json.dumps(articles, indent=2))
    except Exception as e:
        print(f"❌ Tavily Search Tool Exception: {e}")

if __name__ == "__main__":
    print("Starting Isolated Unit Tests for Research Tools...")
    test_fundamentals()
    test_web_search_tavily()
    print("\n🏁 Test Suite Completed.")