"""
research/services/web_search.py — refactored tools/web_search.py
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseSearchProvider(ABC):
    @abstractmethod
    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        pass


class TavilyProvider(BaseSearchProvider):
    def __init__(self, api_key: str = None):
        from django.conf import settings
        self.api_key = api_key or getattr(settings, "TAVILY_API_KEY", "")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not configured.")

    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        res = client.search(
            query=query,
            search_depth="advanced",
            include_images=False,
            include_answer=False,
            include_raw_content=True,
            max_results=max_results,
        )
        out = []
        for r in res.get("results", []) or []:
            title = r.get("title") or ""
            url = r.get("url") or ""
            raw = r.get("raw_content")
            if not raw:
                raw = r.get("content") or ""
            out.append({
                "title": title,
                "url": url,
                "content": raw[:4000]
            })
        return out


class SerperJinaProvider(BaseSearchProvider):
    def __init__(self, serper_api_key: str = None):
        from django.conf import settings
        self.serper_key = serper_api_key or getattr(settings, "SERPER_API_KEY", "")
        if not self.serper_key:
            raise ValueError("SERPER_API_KEY not configured.")

    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        import requests
        headers = {"X-API-KEY": self.serper_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results, "gl": "in"}
        serper_res = requests.post("https://google.serper.dev/search", json=payload, headers=headers).json()
        results = []
        for item in serper_res.get("organic", [])[:max_results]:
            url = item.get("link")
            try:
                jina_res = requests.get(f"https://r.jina.ai/{url}", timeout=10)
                content = jina_res.text[:4000] if jina_res.status_code == 200 else item.get("snippet", "")
            except Exception:
                content = item.get("snippet", "")
            results.append({"title": item.get("title", ""), "url": url, "content": content})
        return results


def tool_deep_web_research(ticker: str, provider: BaseSearchProvider) -> Dict[str, Any]:
    clean_name = ticker.replace(".NS", "").replace(".BO", "")
    queries = [
        f"{clean_name} share latest news analysis earnings probe",
        f"{clean_name} stock brokerage target rating outlook",
        f"{clean_name} management commentary future guidance",
        f"{clean_name} sector headwinds tailwinds competitor analysis",
    ]
    all_articles = []
    for q in queries:
        try:
            all_articles.extend(provider.search_and_extract(query=q, max_results=5))
        except Exception as exc:
            all_articles.append({"title": f"Error: {q}", "url": "", "content": str(exc)})
    return {"ticker": ticker, "total_sources_analyzed": len(all_articles), "articles": all_articles}
