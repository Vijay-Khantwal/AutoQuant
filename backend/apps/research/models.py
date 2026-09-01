from django.db import models
from apps.signals.models import SignalRun


class ResearchRun(models.Model):
    """One execution of the two-tier LLM agent pipeline."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    signal_run = models.ForeignKey(
        SignalRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="research_runs"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    celery_task_id = models.CharField(max_length=255, blank=True)
    log_output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ResearchRun {self.id} [{self.status}]"


class StockDecision(models.Model):
    """Audit verdict for a single stock produced by a ResearchRun."""

    ACTION_CHOICES = [
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
    ]
    run = models.ForeignKey(ResearchRun, on_delete=models.CASCADE, related_name="decisions")
    ticker = models.CharField(max_length=30)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    # Tier 1 output
    tier1_news_brief = models.TextField(blank=True)

    # Tier 2 output
    confidence_score = models.FloatField(default=0.0)
    risk_flags = models.JSONField(default=list)
    fundamental_summary = models.TextField(blank=True)
    news_sentiment_summary = models.TextField(blank=True)
    final_rationale = models.TextField(blank=True)
    recommended_allocation_inr = models.FloatField(default=0.0)

    # Full raw blobs for display
    fundamentals_json = models.JSONField(default=dict)
    raw_verdict_json = models.JSONField(default=dict)

    # Quantitative inputs snapshot
    ltp = models.FloatField(default=0.0)
    win_probability = models.FloatField(default=0.0)
    percentile_rank = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-confidence_score"]

    def __str__(self):
        return f"{self.ticker} → {self.action} (run={self.run_id})"
