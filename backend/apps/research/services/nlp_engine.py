import logging
import threading

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

logger = logging.getLogger(__name__)

class NLPNewsEngine:
    def __init__(self):
        self.model_name = "ProsusAI/finbert"
        self._nlp = None
        self._lock = threading.Lock()

    def _load_model(self):
        if pipeline is None:
            raise ImportError("The 'transformers' and 'torch' libraries are required for NLP. Run: pip install transformers torch")
        
        with self._lock:
            if self._nlp is None:
                logger.info("Loading FinBERT model into memory (this takes a moment)...")
                # Uses CPU by default unless configured for CUDA
                self._nlp = pipeline("sentiment-analysis", model=self.model_name)
        return self._nlp

    def score_headlines(self, headlines: list[str]) -> dict:
        """
        Takes a list of headlines, runs them through FinBERT, and returns an aggregate math score
        from -1.0 (Bearish) to +1.0 (Bullish).
        """
        if not headlines:
            return {"sentiment_score": 0.0, "positive_count": 0, "negative_count": 0, "neutral_count": 0}

        nlp = self._load_model()
        results = nlp(headlines)
        
        score_sum = 0.0
        pos, neg, neu = 0, 0, 0

        for res in results:
            label = res['label']
            score = res['score']  # Confidence (0.0 to 1.0)
            
            if label == 'positive':
                score_sum += score
                pos += 1
            elif label == 'negative':
                score_sum -= score
                neg += 1
            else:
                neu += 1

        avg_score = score_sum / len(headlines) if headlines else 0.0

        return {
            "sentiment_score": round(avg_score, 4),
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "total_articles": len(headlines)
        }

# Singleton instance
nlp_engine = NLPNewsEngine()
