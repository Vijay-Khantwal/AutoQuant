"""Celery tasks for model management."""
import logging
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
def retrain_model_task(self, strategy_id: int):
    """Retrain LightGBM model and persist metrics to DB."""
    from apps.model_mgmt.models import ModelRun, TrainingLog
    from apps.model_mgmt.services import retrain_model

    run = ModelRun.objects.create(celery_task_id=self.request.id, status="RUNNING", strategy_id=strategy_id)

    def log_cb(msg: str):
        TrainingLog.objects.create(model_run=run, log_line=msg)
        _push_log(self.request.id, msg)

    try:
        metrics = retrain_model(strategy_id=strategy_id, log_callback=log_cb)
        fold_metrics = metrics.get("fold_metrics", [])

        update_fields = {
            "status": "SUCCESS",
            "feature_importances": metrics.get("feature_importances", {}),
            "total_samples": metrics.get("total_samples"),
            "total_stocks": metrics.get("total_stocks"),
            "trained_at": datetime.now(),
        }
        if len(fold_metrics) >= 1:
            update_fields["fold1_base_rate"] = fold_metrics[0].get("base_rate")
            update_fields["fold1_precision"] = fold_metrics[0].get("precision")
        if len(fold_metrics) >= 2:
            update_fields["fold2_base_rate"] = fold_metrics[1].get("base_rate")
            update_fields["fold2_precision"] = fold_metrics[1].get("precision")
        if len(fold_metrics) >= 3:
            update_fields["fold3_base_rate"] = fold_metrics[2].get("base_rate")
            update_fields["fold3_precision"] = fold_metrics[2].get("precision")

        for attr, val in update_fields.items():
            setattr(run, attr, val)
        run.save()

        _push_log(self.request.id, "DONE")
        return {"status": "success", "run_id": run.id}

    except Exception as exc:
        logger.error("Retrain task failed: %s", exc)
        run.status = "FAILED"
        run.notes = str(exc)
        run.save(update_fields=["status", "notes"])
        _push_log(self.request.id, f"ERROR: {exc}")
        raise
