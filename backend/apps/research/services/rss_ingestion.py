import feedparser
import logging
from datetime import datetime, timezone
from time import mktime
from django.utils.timezone import make_aware, is_naive
from apps.research.models import NewsArticle
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

# Primary feeds for Indian Markets
RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/buzzingstocks.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml"
]

def fetch_rss_feeds():
    """Fetches RSS feeds and caches them in the NewsArticle table."""
    new_articles = 0
    for feed_url in RSS_FEEDS:
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                # Basic parsing
                title = entry.get('title', '').strip()
                url = entry.get('link', '').strip()
                summary_raw = entry.get('summary', '')
                
                # Clean HTML from summary
                soup = BeautifulSoup(summary_raw, "html.parser")
                summary = soup.get_text(separator=' ', strip=True)
                
                # Parse date
                pub_date = entry.get('published_parsed')
                if pub_date:
                    dt = datetime.fromtimestamp(mktime(pub_date))
                    if is_naive(dt):
                        dt = make_aware(dt, timezone.utc)
                else:
                    dt = datetime.now(timezone.utc)
                    
                # Skip if already exists
                if NewsArticle.objects.filter(url=url).exists():
                    continue
                    
                # Attempt to extract ticker if it's explicitly mentioned (Very naive check for NSE format)
                # In a real system, we'd use SpaCy or a quick regex on known NSE tickers.
                # For this step, we leave it blank, and the web_search fallback will match by keywords.
                
                NewsArticle.objects.create(
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=dt,
                    source=feed_url.split('/')[2]
                )
                new_articles += 1
                
        except Exception as e:
            logger.error(f"Error fetching {feed_url}: {e}")
            
    logger.info(f"Ingested {new_articles} new articles from RSS feeds.")
    return new_articles

def fetch_yfinance_news_for_ticker(ticker):
    """Specifically fetches news for a given ticker from Yahoo Finance to augment RSS."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        news = t.news
        new_count = 0
        for n in news:
            content = n.get('content', {})
            title = content.get('title', '')
            url = content.get('canonicalUrl', {}).get('url', '')
            summary = content.get('summary', '')
            pub_date_str = content.get('pubDate')
            
            if not title or not url:
                continue
                
            if NewsArticle.objects.filter(url=url).exists():
                continue
                
            dt = datetime.now(timezone.utc)
            if pub_date_str:
                try:
                    # yfinance usually gives ISO format
                    dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            NewsArticle.objects.create(
                ticker=ticker,
                title=title,
                url=url,
                summary=summary,
                published_at=dt,
                source='yfinance'
            )
            new_count += 1
        return new_count
    except Exception as e:
        logger.error(f"Failed to fetch yfinance news for {ticker}: {e}")
        return 0

