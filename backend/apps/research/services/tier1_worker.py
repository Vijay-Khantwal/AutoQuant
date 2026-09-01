"""
research/services/tier1_worker.py
StepFun 3.7 Flash — fast news distiller (Tier 1 LLM).
"""
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


def get_nim_client() -> OpenAI:
    return OpenAI(base_url=settings.NIM_BASE_URL, api_key=settings.NVIDIA_API_KEY)


def distill_news_articles(ticker: str, web_data: dict) -> str:
    """Tier 1: reads raw articles and extracts hard financial facts."""
    articles = web_data.get("articles", [])
    if not articles:
        return "No recent news articles found."

    raw_text = "\n\n---\n\n".join(
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
{raw_text}
"""
    try:
        logger.info("  [Tier 1] Distilling news via LLM for %s...", ticker)
        client = get_nim_client()
        response = client.chat.completions.create(
            model=settings.NVIDIA_FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=8000,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "No summary generated."
    except Exception as exc:
        logger.error("Tier 1 worker failed for %s: %s", ticker, exc)
        return f"Worker Extraction Failed: {exc}"
