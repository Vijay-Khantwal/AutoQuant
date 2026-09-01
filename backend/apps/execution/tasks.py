"""Celery tasks for the execution app."""
import logging

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
def run_execution_task(self, decision_ids: list = None, research_run_id: int = None):
    """
    Execute approved trades via Dhan Sandbox.
    decision_ids: explicit list of StockDecision PKs to execute (for manual selection).
    research_run_id: execute all APPROVE decisions from this run if decision_ids is None.
    """
    from apps.research.models import StockDecision, ResearchRun
    from apps.execution.models import ExecutionRun, Order
    from apps.execution.services.dhan_mapper import get_dhan_security_id
    from apps.execution.services.dhan_client import place_order
    from apps.execution.services.fee_engine import get_entry_fees
    from apps.portfolio.models import Position
    from django.conf import settings
    import datetime

    run = ExecutionRun.objects.create(celery_task_id=self.request.id, status="RUNNING")
    if research_run_id:
        try:
            run.research_run = ResearchRun.objects.get(id=research_run_id)
            run.save(update_fields=["research_run"])
        except ResearchRun.DoesNotExist:
            pass

    def log(msg: str):
        run.log_output += msg + "\n"
        run.save(update_fields=["log_output"])
        _push_log(self.request.id, msg)

    try:
        # Resolve which decisions to execute
        if decision_ids:
            decisions = StockDecision.objects.filter(id__in=decision_ids)
        elif research_run_id:
            decisions = StockDecision.objects.filter(run_id=research_run_id)
        else:
            # Latest research run
            latest = ResearchRun.objects.filter(status="SUCCESS").first()
            if not latest:
                raise ValueError("No successful research run found.")
            decisions = StockDecision.objects.filter(run=latest)

        log(f"Executing {decisions.count()} requested decisions (including rejects)...")
        capital = settings.CAPITAL_PER_TRADE_INR

        for dec in decisions:
            alloc = dec.recommended_allocation_inr
            if not alloc or alloc <= 0:
                alloc = capital
                
            qty = int(alloc / dec.ltp) if dec.ltp > 0 else 0

            if qty <= 0:
                log(f"  ⏭️  {dec.ticker}: qty=0, skipping.")
                continue

            log(f"  ⚙️  {dec.ticker}: qty={qty} | alloc=₹{alloc:.0f}")

            try:
                dhan_id = get_dhan_security_id(dec.ticker)
            except ValueError as exc:
                log(f"  ❌ {dec.ticker}: ID lookup failed — {exc}")
                Order.objects.create(
                    run=run, decision=dec, ticker=dec.ticker,
                    quantity=qty, price=dec.ltp, allocated_inr=alloc,
                    dhan_status="ERROR", dhan_raw_response={"error": str(exc)},
                )
                continue

            try:
                resp = place_order(
                    security_id=dhan_id,
                    quantity=qty,
                    transaction_type="BUY",
                    correlation_id=f"AUDIT-{dec.id}"
                )
                
                order_status = resp.get("orderStatus", "ERROR")
                
                # Fetch entry fees
                from apps.execution.services.fee_engine import get_entry_fees
                entry_fees = get_entry_fees(dec.ltp, qty)

                order = Order.objects.create(
                    run=run,
                    decision=dec,
                    ticker=dec.ticker,
                    dhan_security_id=dhan_id,
                    quantity=qty,
                    price=dec.ltp,
                    allocated_inr=alloc,
                    transaction_type="BUY",
                    dhan_order_id=resp.get("orderId", ""),
                    dhan_status=order_status,
                    dhan_raw_response=resp,
                    fee_zerodha=entry_fees["zerodha"],
                    fee_dhan=entry_fees["dhan"],
                    fee_groww=entry_fees["groww"],
                    fee_angel=entry_fees["angel"],
                )
                
                if order_status in ["PENDING", "TRADED", "TRANSIT"]:
                    log(f"[{dec.ticker}]: ORDER PLACED — Dhan ID: {resp.get('orderId')}")
                    # Open a paper position
                    import datetime as dt
                    strategy = dec.run.signal_run.strategy if dec.run and dec.run.signal_run else None
                    tp_target = strategy.tp_target if strategy else 0.03
                    sl_stop = strategy.sl_stop if strategy else -0.02
                    hold_days = strategy.hold_days if strategy else 15
                    
                    tp_price = dec.ltp * (1 + tp_target)
                    sl_price = dec.ltp * (1 + sl_stop)
                    Position.objects.create(
                        strategy=strategy,
                        ai_decision=dec.action,
                        ticker=dec.ticker,
                        entry_price=dec.ltp,
                        current_price=dec.ltp,
                        quantity=qty,
                        entry_date=dt.date.today(),
                        entry_order=order,
                        tp_price=round(tp_price, 2),
                        sl_price=round(sl_price, 2),
                        max_hold_days=hold_days,
                        status="OPEN",
                    )
                else:
                    log(f"[{dec.ticker}]: REJECTED — {resp}")
            except Exception as e:
                log(f"  Error executing {dec.ticker}: {e}")
                continue

        run.status = "SUCCESS"
        run.save(update_fields=["status"])
        _push_log(self.request.id, "DONE")
        return {"status": "success", "run_id": run.id}

    except Exception as exc:
        logger.error("Execution task failed: %s", exc)
        run.status = "FAILED"
        run.log_output += f"\nERROR: {exc}"
        run.save(update_fields=["status", "log_output"])
        _push_log(self.request.id, f"ERROR: {exc}")
        raise


@shared_task(bind=True)
def autonomous_daily_pipeline_task(self):
    """
    Master cron job to run the entire pipeline end-to-end:
    1. Predict (Signals)
    2. Research top 5 (AI Audit)
    3. Execute all 5
    """
    from apps.signals.models import SignalRun, Signal
    from apps.signals.services import run_prediction
    from apps.research.models import ResearchRun
    from apps.research.tasks import run_research_task
    from apps.execution.tasks import run_execution_task

    from apps.model_mgmt.models import StrategyProfile

    active_strategies = StrategyProfile.objects.filter(is_active=True)
    if not active_strategies.exists():
        logger.error("No active strategies found for autonomous pipeline.")
        return

    logger.info("--- STARTING AUTONOMOUS PIPELINE ---")
    
    for strategy in active_strategies:
        logger.info(f"== Processing Strategy: {strategy.name} ==")
        
        # Step 1: Predict
        logger.info("Step 1: Running ML Prediction...")
        sig_run = SignalRun.objects.create(status="RUNNING", strategy=strategy)
        try:
            signals = run_prediction(strategy_id=strategy.id, log_callback=lambda msg: None)
            Signal.objects.bulk_create([
                Signal(run=sig_run, ticker=s["ticker"], ltp=s["ltp"], 
                       win_probability=s["win_probability"], percentile_rank=s["percentile_rank"], rank=s["rank"])
                for s in signals
            ])
            sig_run.status = "SUCCESS"
            sig_run.save()
        except Exception as e:
            sig_run.status = "FAILED"
            sig_run.save()
            logger.error(f"Auto Pipeline failed at Prediction for {strategy.name}: {e}")
            continue

        # Grab Top 5
        top_signals = Signal.objects.filter(run=sig_run).order_by("rank")[:5]
        tickers = [s.ticker for s in top_signals]
        logger.info(f"Top 5 selected: {tickers}")

        # Step 2: Research
        logger.info("Step 2: Running AI Audit (Synchronously for cron)...")
        res_run = ResearchRun.objects.create(signal_run=sig_run, status="RUNNING")
        
        try:
            run_research_task.apply(kwargs={
                "signal_run_id": sig_run.id,
                "research_run_id": res_run.id,
                "top_n": 5,
                "ticker_list": tickers
            })
        except Exception as e:
            logger.error(f"Auto Pipeline failed at Research for {strategy.name}: {e}")
            continue

        # Step 3: Execute
        logger.info("Step 3: Executing all 5 decisions...")
        try:
            run_execution_task.apply(kwargs={"research_run_id": res_run.id})
        except Exception as e:
            logger.error(f"Auto Pipeline failed at Execution for {strategy.name}: {e}")
            continue

    logger.info("--- AUTONOMOUS PIPELINE COMPLETE ---")


