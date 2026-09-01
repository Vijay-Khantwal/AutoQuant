"""Celery tasks for the signals app."""
import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def _push_log(task_id: str, message: str):
    """Send a log line to the WebSocket group for this task."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"task_{task_id}",
        {"type": "task.log", "message": message},
    )


@shared_task(bind=True)
def run_prediction_task(self, strategy_id: int):
    """Run the full ML prediction pipeline and save results to DB."""
    from apps.signals.models import SignalRun, Signal
    from apps.signals.services import run_prediction

    run = SignalRun.objects.create(celery_task_id=self.request.id, status="RUNNING", strategy_id=strategy_id)

    def log_cb(msg):
        run.log_output += msg + "\n"
        run.save(update_fields=["log_output"])
        _push_log(self.request.id, msg)

    try:
        signals = run_prediction(strategy_id=strategy_id, log_callback=log_cb)
        Signal.objects.bulk_create([
            Signal(
                run=run,
                ticker=s["ticker"],
                ltp=s["ltp"],
                win_probability=s["win_probability"],
                percentile_rank=s["percentile_rank"],
                rank=s["rank"],
            )
            for s in signals
        ])
        run.status = "SUCCESS"
        run.save(update_fields=["status"])
        _push_log(self.request.id, "DONE")
        return {"status": "success", "run_id": run.id, "count": len(signals)}
    except Exception as exc:
        logger.error("Prediction task failed: %s", exc)
        run.status = "FAILED"
        run.log_output += f"\nERROR: {exc}"
        run.save(update_fields=["status", "log_output"])
        _push_log(self.request.id, f"ERROR: {exc}")
        raise
