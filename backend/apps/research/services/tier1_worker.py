"""
research/services/tier1_worker.py
StepFun 3.7 Flash — fast news distiller (Tier 1 LLM).
"""
import logging
from openai import OpenAI, AzureOpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


def get_llm_client():
    if settings.LLM_PROVIDER == "azure":
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            max_retries=3
        )
        model = settings.AZURE_OPENAI_FAST_DEPLOYMENT_NAME
    else:
        client = OpenAI(
            base_url=settings.NIM_BASE_URL, 
            api_key=settings.NVIDIA_API_KEY,
            max_retries=3
        )
        model = settings.NVIDIA_FAST_MODEL
    return client, model


def distill_news_articles(ticker: str, web_data: dict) -> dict:
    """Tier 1: reads raw articles and extracts broad, nuanced facts."""
    articles = web_data.get("articles", [])
    if not articles:
        return {"bullet_points": "No recent news articles found."}

    raw_text = "\n\n---\n\n".join(
        [f"Title: {a['title']}\nContent: {a['content'][:3000]}" for a in articles]
    )
    prompt = f"""
You are an expert financial analyst. Read the following recent articles for {ticker}.
Write a highly precise, broad, and nuanced executive summary of the current situation. 
Capture the true context: catalysts, risks, management tone, and macroeconomic tailwinds/headwinds.

Do not force the text into arbitrary buckets. Present a rich, cohesive bulleted summary that a human Portfolio Manager would read to understand the exact reality of the business right now.

Raw Articles:
{raw_text}
"""
    try:
        logger.info("  [Tier 1] Distilling broad news context for %s...", ticker)
        client, target_model = get_llm_client()
        response = client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=8000,
        )
        content = response.choices[0].message.content
        if not content:
            return {"bullet_points": "No summary generated."}
            
        return {"bullet_points": content.strip()}
    except Exception as exc:
        logger.error("Tier 1 worker failed for %s: %s", ticker, exc)
        return {"bullet_points": f"Worker Extraction Failed: {exc}"}
