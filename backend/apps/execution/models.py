from django.db import models
from apps.research.models import ResearchRun, StockDecision


class ExecutionRun(models.Model):
    """One execution of the Dhan order placement pipeline."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("PARTIAL", "Partial"),
        ("FAILED", "Failed"),
    ]
    research_run = models.ForeignKey(
        ResearchRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="execution_runs"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    celery_task_id = models.CharField(max_length=255, blank=True)
    log_output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ExecutionRun {self.id} [{self.status}]"


class Order(models.Model):
    """A single order placed (or attempted) via the Dhan Sandbox API."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("TRANSIT", "Transit"),
        ("TRADED", "Traded"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
        ("ERROR", "Error"),
    ]
    run = models.ForeignKey(ExecutionRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    decision = models.ForeignKey(StockDecision, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    ticker = models.CharField(max_length=30)
    dhan_security_id = models.CharField(max_length=30, blank=True)
    quantity = models.IntegerField(default=0)
    price = models.FloatField(default=0.0)          # entry price at time of order
    allocated_inr = models.FloatField(default=0.0)
    transaction_type = models.CharField(max_length=4, default="BUY")  # BUY or SELL

    dhan_order_id = models.CharField(max_length=100, blank=True)
    dhan_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    dhan_raw_response = models.JSONField(default=dict)

    # Fee breakdown per broker (populated by fee_engine)
    fee_zerodha = models.FloatField(default=0.0)
    fee_dhan    = models.FloatField(default=0.0)
    fee_groww   = models.FloatField(default=0.0)
    fee_angel   = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.ticker} {self.transaction_type} x{self.quantity} [{self.dhan_status}]"
