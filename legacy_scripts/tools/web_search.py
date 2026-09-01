import os
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables automatically
load_dotenv()

# ---------------------------------------------------------
# 1. ABSTRACT SEARCH INTERFACE
# ---------------------------------------------------------
class BaseSearchProvider(ABC):
    @abstractmethod
    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        pass

# ---------------------------------------------------------
# 2. TAVILY IMPLEMENTATION
# ---------------------------------------------------------
class TavilyProvider(BaseSearchProvider):
    def __init__(self, api_key: str = None):
        # Reads from .env if not passed explicitly
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Tavily API key missing. Ensure TAVILY_API_KEY is defined in your .env file.")
        
        from tavily import TavilyClient
        self.client = TavilyClient(api_key=self.api_key)

    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        response = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_raw_content=False
        )
        
        results = []
        for item in response.get('results', []):
            results.append({
                "title": item.get('title', ''),
                "url": item.get('url', ''),
                "content": item.get('content', '')
            })
        return results

# ---------------------------------------------------------
# 3. SERPER + JINA IMPLEMENTATION
# ---------------------------------------------------------
class SerperJinaProvider(BaseSearchProvider):
    def __init__(self, serper_api_key: str = None):
        self.serper_key = serper_api_key or os.getenv("SERPER_API_KEY")
        if not self.serper_key:
            raise ValueError("Serper API key missing. Ensure SERPER_API_KEY is defined in your .env file.")

    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        headers = {"X-API-KEY": self.serper_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results, "gl": "in"}
        serper_res = requests.post("https://google.serper.dev/search", json=payload, headers=headers).json()
        
        results = []
        for item in serper_res.get('organic', [])[:max_results]:
            url = item.get('link')
            jina_url = f"https://r.jina.ai/{url}"
            try:
                jina_res = requests.get(jina_url, timeout=10)
                full_text = jina_res.text[:4000] if jina_res.status_code == 200 else item.get('snippet', '')
            except Exception:
                full_text = item.get('snippet', '')
                
            results.append({
                "title": item.get('title', ''),
                "url": url,
                "content": full_text
            })
        return results

# ---------------------------------------------------------
# 4. DEEP WEB RESEARCH TOOL FUNCTION
# ---------------------------------------------------------
def tool_deep_web_research(ticker: str, provider: BaseSearchProvider) -> Dict[str, Any]:
    clean_name = ticker.replace('.NS', '').replace('.BO', '')
    
    queries = [
        f"{clean_name} share latest news analysis earnings probe",
        f"{clean_name} stock brokerage target rating outlook"
    ]
    
    all_articles = []
    for q in queries:
        try:
            articles = provider.search_and_extract(query=q, max_results=3)
            all_articles.extend(articles)
        except Exception as e:
            all_articles.append({"title": f"Error running query '{q}'", "url": "", "content": str(e)})

    return {
        "ticker": ticker,
        "total_sources_analyzed": len(all_articles),
        "articles": all_articles
    }