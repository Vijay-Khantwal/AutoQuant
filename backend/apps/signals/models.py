from django.db import models
from apps.model_mgmt.models import StrategyProfile


class SignalRun(models.Model):
    """One execution of predict.py — produces a ranked list of signals."""

    strategy = models.ForeignKey(StrategyProfile, on_delete=models.CASCADE, null=True, related_name="signal_runs")
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    run_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    celery_task_id = models.CharField(max_length=255, blank=True)
    log_output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SignalRun {self.run_date} [{self.status}]"


class Signal(models.Model):
    """Individual stock signal produced by a SignalRun."""

    run = models.ForeignKey(SignalRun, on_delete=models.CASCADE, related_name="signals")
    ticker = models.CharField(max_length=30)
    ltp = models.FloatField()
    win_probability = models.FloatField()
    percentile_rank = models.FloatField()
    rank = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"{self.ticker} (run={self.run_id}, rank={self.rank})"
