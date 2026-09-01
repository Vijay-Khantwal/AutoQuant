"""Celery tasks for the research app."""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def _push_log(task_id: str, message: str):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"task_{task_id}",
        {"type": "task.log", "message": message},
    )


@shared_task(bind=True)
def run_research_task(self, signal_run_id: int = None, research_run_id: int = None, top_n: int = 10, ticker_list: list = None):
    """Run two-tier LLM agent pipeline on specific signals."""
    from apps.signals.models import SignalRun, Signal
    from apps.research.models import ResearchRun, StockDecision
    from apps.research.services.fundamentals import tool_deep_fundamentals
    from apps.research.services.web_search import TavilyProvider, tool_deep_web_research
    from apps.research.services.tier1_worker import distill_news_articles
    from apps.research.services.tier2_auditor import audit_stock
    from django.conf import settings

    if research_run_id:
        run = ResearchRun.objects.get(id=research_run_id)
        run.status = "RUNNING"
        run.celery_task_id = self.request.id
        run.save()
        signal_run = run.signal_run
    else:
        # Resolve signal run
        signal_run = None
        if signal_run_id:
            try:
                signal_run = SignalRun.objects.get(id=signal_run_id)
            except SignalRun.DoesNotExist:
                pass

        run = ResearchRun.objects.create(
            celery_task_id=self.request.id,
            status="RUNNING",
            signal_run=signal_run,
        )

    def log(msg: str):
        run.log_output += msg + "\n"
        run.save(update_fields=["log_output"])
        _push_log(self.request.id, msg)

    try:
        # Get candidates from latest signal run
        if signal_run:
            candidates_qs = Signal.objects.filter(run=signal_run).order_by("rank")
        else:
            latest_run = SignalRun.objects.filter(status="SUCCESS").first()
            if not latest_run:
                raise ValueError("No successful signal run found. Run prediction first.")
            signal_run = latest_run
            run.signal_run = signal_run
            run.save()
            candidates_qs = Signal.objects.filter(run=latest_run).order_by("rank")
        
        if ticker_list:
            candidates_qs = candidates_qs.filter(ticker__in=ticker_list)
        else:
            candidates_qs = candidates_qs[:top_n]

        candidates = list(candidates_qs)
        log(f"Starting two-tier audit on {len(candidates)} candidates...")

        search_engine = TavilyProvider()

        def process_one(sig):
            ticker = sig.ticker
            log(f"[1/3] {ticker}: Gathering data...")
            fund_data = tool_deep_fundamentals(ticker)
            web_data = tool_deep_web_research(ticker, provider=search_engine)

            dossier = {
                "metadata": {"ticker": ticker, "research_timestamp": datetime.now().isoformat()},
                "quantitative_inputs": {
                    "ltp": sig.ltp,
                    "ml_win_probability": sig.win_probability,
                    "percentile_rank": sig.percentile_rank,
                },
                "fundamentals": fund_data,
            }

            log(f"[2/3] {ticker}: Tier 1 distilling news...")
            news_brief = distill_news_articles(ticker, web_data)

            log(f"[3/3] {ticker}: Tier 2 auditing...")
            verdict = audit_stock(dossier, news_brief)
            
            # Save immediately so the UI can incrementally fill
            StockDecision.objects.create(
                run=run,
                ticker=ticker,
                action=verdict.get("decision", "REJECT"),
                tier1_news_brief=news_brief,
                confidence_score=verdict.get("confidence_score", 0.0),
                risk_flags=verdict.get("risk_flags", []),
                fundamental_summary=verdict.get("fundamental_summary", ""),
                news_sentiment_summary=verdict.get("news_and_sentiment_summary", ""),
                final_rationale=verdict.get("final_rationale", ""),
                recommended_allocation_inr=verdict.get("recommended_allocation_inr", 0),
                fundamentals_json=dossier.get("fundamentals", {}),
                raw_verdict_json=verdict,
                ltp=dossier["quantitative_inputs"]["ltp"],
                win_probability=dossier["quantitative_inputs"]["ml_win_probability"],
                percentile_rank=dossier["quantitative_inputs"]["percentile_rank"],
            )
            log(f"{ticker}: {verdict.get('decision')} (confidence={verdict.get('confidence_score', 0):.2f})")
            return True

        with ThreadPoolExecutor(max_workers=min(3, len(candidates))) as pool:
            # list() forces the threadpool to execute and wait for all
            list(pool.map(process_one, candidates))

        run.status = "SUCCESS"
        run.save(update_fields=["status"])
        _push_log(self.request.id, "DONE")
        return {"status": "success", "run_id": run.id}

    except Exception as exc:
        logger.error("Research task failed: %s", exc)
        run.status = "FAILED"
        run.log_output += f"\nERROR: {exc}"
        run.save(update_fields=["status", "log_output"])
        _push_log(self.request.id, f"ERROR: {exc}")
        raise

@shared_task(bind=True)
def rerun_single_stock_task(self, decision_id: int):
    try:
        from apps.research.models import StockDecision
        from apps.research.services.fundamentals import tool_deep_fundamentals
        from apps.research.services.web_search import tool_deep_web_research
        from apps.research.services.tier1_worker import distill_news_articles
        from apps.research.services.tier2_auditor import audit_stock
        from django.conf import settings
        
        dec = StockDecision.objects.get(id=decision_id)
        ticker = dec.ticker
        
        def log(msg: str):
            logger.info(msg)
            _push_log(self.request.id, msg)

        log(f'[1/3] {ticker}: Re-gathering data...')
        fund_data = tool_deep_fundamentals(ticker)
        search_provider = getattr(settings, "SEARCH_PROVIDER", "tavily")
        if search_provider == "serper":
            from .services.web_search import SerperJinaProvider
            search_engine = SerperJinaProvider()
        else:
            from .services.web_search import TavilyProvider
            search_engine = TavilyProvider()
        web_data = tool_deep_web_research(ticker, provider=search_engine)

        dossier = {
            'metadata': {'ticker': ticker, 'research_timestamp': datetime.now().isoformat()},
            'quantitative_inputs': {
                'ltp': dec.ltp,
                'ml_win_probability': dec.win_probability,
                'percentile_rank': dec.percentile_rank,
            },
            'fundamentals': fund_data,
        }

        log(f'[2/3] {ticker}: Tier 1 distilling news...')
        news_brief = distill_news_articles(ticker, web_data)

        log(f'[3/3] {ticker}: Tier 2 auditing...')
        verdict = audit_stock(dossier, news_brief)
        
        # Update the existing decision
        dec.action = verdict.get('decision', 'REJECT')
        dec.tier1_news_brief = news_brief
        dec.confidence_score = verdict.get('confidence_score', 0.0)
        dec.risk_flags = verdict.get('risk_flags', [])
        dec.fundamental_summary = verdict.get('fundamental_summary', '')
        dec.news_sentiment_summary = verdict.get('news_and_sentiment_summary', '')
        dec.final_rationale = verdict.get('final_rationale', '')
        dec.recommended_allocation_inr = verdict.get('recommended_allocation_inr', 0)
        dec.fundamentals_json = dossier.get('fundamentals', {})
        dec.raw_verdict_json = verdict
        dec.save()
        
        _push_log(self.request.id, "DONE")
        return {'status': 'success', 'decision_id': dec.id}
    except Exception as exc:
        logger.error('Rerun task failed: %s', exc)
        _push_log(self.request.id, f"ERROR: {exc}")
        raise

